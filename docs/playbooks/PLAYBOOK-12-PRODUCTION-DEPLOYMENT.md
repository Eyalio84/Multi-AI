# Playbook 12: Production Deployment & Operations

**Version:** 1.0
**Created:** November 27, 2025
**Category:** Operations
**Prerequisites:** PB 1 (Cost), PB 3 (Agents), PB 10 (MCP Servers)

---

## Executive Summary

This playbook bridges the gap between development and production for NLKE-based systems. It covers deployment, monitoring, error handling, and operational excellence for MCP servers, agents, and knowledge graphs.

**Core Principle:** Development patterns that work locally need additional infrastructure for production reliability.

---

## Table of Contents

1. [Production Architecture Patterns](#1-production-architecture-patterns)
2. [Deployment Strategies](#2-deployment-strategies)
3. [Monitoring & Observability](#3-monitoring--observability)
4. [Error Handling & Recovery](#4-error-handling--recovery)
5. [API Quota Management](#5-api-quota-management)
6. [Backup & Disaster Recovery](#6-backup--disaster-recovery)
7. [Performance Tuning](#7-performance-tuning)
8. [Operational Runbooks](#8-operational-runbooks)

---

## 1. Production Architecture Patterns

### 1.1 High Availability MCP Server Architecture

```
                    Load Balancer
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     MCP Server 1   MCP Server 2   MCP Server 3
          │              │              │
          └──────────────┼──────────────┘
                         │
                   Shared State
              ┌──────────┼──────────┐
              │          │          │
         SQLite      Embeddings   Cache
         (Primary)   (Replicated) (Redis)
```

### 1.2 Container Configuration

```dockerfile
# Dockerfile for MCP Server
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY nlke_mcp/ ./nlke_mcp/
COPY gemini-kg/ ./gemini-kg/
COPY claude_kg_truth/ ./claude_kg_truth/

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run server
CMD ["python", "-m", "nlke_mcp.servers.nlke_unified_server"]

EXPOSE 8080
```

### 1.3 Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nlke-mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nlke-mcp
  template:
    metadata:
      labels:
        app: nlke-mcp
    spec:
      containers:
      - name: mcp-server
        image: nlke-mcp:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: DB_PATH
          value: "/data/kg.db"
        volumeMounts:
        - name: kg-data
          mountPath: /data
      volumes:
      - name: kg-data
        persistentVolumeClaim:
          claimName: kg-data-pvc
```

---

## 2. Deployment Strategies

### 2.1 Progressive Rollout

```python
class ProgressiveRollout:
    """
    Deploy new versions progressively to minimize risk.

    Stages:
    1. Internal (10 req/day, manual validation)
    2. Beta (100 req/day, automated monitoring)
    3. Limited GA (1000 req/day, canary deployment)
    4. Full (unlimited, blue-green deployment)
    """

    STAGES = {
        "internal": {
            "max_requests": 10,
            "validation": "manual",
            "rollback_threshold": 0.5  # 50% error rate
        },
        "beta": {
            "max_requests": 100,
            "validation": "automated",
            "rollback_threshold": 0.1  # 10% error rate
        },
        "limited_ga": {
            "max_requests": 1000,
            "validation": "automated",
            "rollback_threshold": 0.05  # 5% error rate
        },
        "production": {
            "max_requests": None,
            "validation": "monitoring",
            "rollback_threshold": 0.02  # 2% error rate
        }
    }

    def __init__(self, current_stage: str = "internal"):
        self.stage = current_stage
        self.metrics = defaultdict(int)

    def can_advance(self) -> bool:
        """Check if ready for next stage."""
        config = self.STAGES[self.stage]

        total = self.metrics["success"] + self.metrics["error"]
        if total < config["max_requests"]:
            return False

        error_rate = self.metrics["error"] / total if total > 0 else 0
        return error_rate < config["rollback_threshold"]

    def should_rollback(self) -> bool:
        """Check if rollback needed."""
        config = self.STAGES[self.stage]

        total = self.metrics["success"] + self.metrics["error"]
        if total < 10:  # Need minimum sample
            return False

        error_rate = self.metrics["error"] / total
        return error_rate >= config["rollback_threshold"]
```

### 2.2 Blue-Green Deployment

```python
class BlueGreenDeployer:
    """
    Zero-downtime deployment with instant rollback capability.
    """

    def __init__(self, load_balancer):
        self.lb = load_balancer
        self.active = "blue"
        self.standby = "green"

    async def deploy(self, new_version: str):
        """Deploy new version to standby, then switch."""

        # 1. Deploy to standby
        await self.deploy_to_environment(self.standby, new_version)

        # 2. Run health checks
        if not await self.health_check(self.standby):
            raise DeploymentError(f"Health check failed for {self.standby}")

        # 3. Run smoke tests
        if not await self.smoke_test(self.standby):
            raise DeploymentError(f"Smoke tests failed for {self.standby}")

        # 4. Switch traffic
        await self.lb.switch_traffic(self.standby)

        # 5. Update state
        self.active, self.standby = self.standby, self.active

        return {"status": "success", "active": self.active}

    async def rollback(self):
        """Instant rollback to previous version."""
        await self.lb.switch_traffic(self.standby)
        self.active, self.standby = self.standby, self.active
        return {"status": "rolled_back", "active": self.active}
```

---

## 3. Monitoring & Observability

### 3.1 Health Check Endpoints

```python
from datetime import datetime
import psutil

class HealthMonitor:
    """
    Production health monitoring for MCP servers.
    """

    def __init__(self, kg_connection, embedding_model):
        self.kg = kg_connection
        self.model = embedding_model
        self.last_query_time = None
        self.start_time = datetime.now()

    def health_check(self) -> dict:
        """Basic health check - is the service alive?"""
        return {
            "status": "healthy",
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "timestamp": datetime.now().isoformat()
        }

    def readiness_check(self) -> dict:
        """Readiness check - is the service ready to serve?"""
        checks = {
            "kg_connected": self._check_kg(),
            "embeddings_loaded": self._check_embeddings(),
            "memory_ok": self._check_memory()
        }

        all_ready = all(checks.values())

        return {
            "ready": all_ready,
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }

    def detailed_status(self) -> dict:
        """Detailed status for debugging."""
        return {
            "health": self.health_check(),
            "readiness": self.readiness_check(),
            "metrics": {
                "kg_nodes": self.kg.node_count() if self.kg else 0,
                "kg_edges": self.kg.edge_count() if self.kg else 0,
                "embeddings_count": len(self.model.embeddings) if self.model else 0,
                "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_percent": psutil.Process().cpu_percent(),
                "last_query_age_seconds": (
                    (datetime.now() - self.last_query_time).total_seconds()
                    if self.last_query_time else None
                )
            }
        }

    def _check_kg(self) -> bool:
        try:
            self.kg.execute("SELECT 1")
            return True
        except:
            return False

    def _check_embeddings(self) -> bool:
        return self.model is not None and len(self.model.embeddings) > 0

    def _check_memory(self) -> bool:
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        return memory_mb < 1800  # Under 1.8GB limit
```

### 3.2 Metrics Collection (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
QUERY_LATENCY = Histogram(
    'nlke_query_latency_seconds',
    'Query latency in seconds',
    ['tool_name', 'status']
)

QUERY_COUNT = Counter(
    'nlke_query_total',
    'Total queries processed',
    ['tool_name', 'status']
)

KG_NODE_COUNT = Gauge(
    'nlke_kg_nodes_total',
    'Total nodes in knowledge graph',
    ['kg_name']
)

ACTIVE_CONNECTIONS = Gauge(
    'nlke_active_connections',
    'Number of active connections'
)

class MetricsMiddleware:
    """Middleware to collect metrics for all tool calls."""

    async def __call__(self, tool_name: str, handler, arguments: dict):
        start_time = time.time()
        status = "success"

        try:
            result = await handler(arguments)
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            QUERY_LATENCY.labels(tool_name=tool_name, status=status).observe(duration)
            QUERY_COUNT.labels(tool_name=tool_name, status=status).inc()
```

### 3.3 Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: nlke-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(nlke_query_total{status="error"}[5m]) / rate(nlke_query_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in NLKE queries"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(nlke_query_latency_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High query latency"
          description: "P95 latency is {{ $value }}s"

      - alert: LowKGNodeCount
        expr: nlke_kg_nodes_total < 100
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Knowledge graph has too few nodes"
          description: "Only {{ $value }} nodes in KG"

      - alert: MemoryHigh
        expr: process_resident_memory_bytes > 1.8e9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory at {{ $value | humanize1024 }}"
```

---

## 4. Error Handling & Recovery

### 4.1 Circuit Breaker Pattern

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """
    Prevent cascade failures with circuit breaker pattern.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        success_threshold: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout)
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def can_execute(self) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout passed
            if datetime.now() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False

        # HALF_OPEN - allow limited requests
        return True

    def record_success(self):
        """Record successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0

    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    async def execute(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if not self.can_execute():
            raise CircuitOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
```

### 4.2 Retry with Exponential Backoff

```python
import asyncio
import random

class RetryPolicy:
    """
    Configurable retry policy with exponential backoff.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            delay = delay * (0.5 + random.random())

        return delay

    async def execute(self, func, *args, retryable_exceptions=(Exception,), **kwargs):
        """Execute function with retry policy."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = self.get_delay(attempt)
                    await asyncio.sleep(delay)

        raise last_exception
```

### 4.3 Graceful Degradation

```python
class GracefulDegradation:
    """
    Cascade to fallback options when primary fails.
    """

    def __init__(self):
        self.fallback_chain = [
            {
                "name": "Claude Opus 4.5",
                "handler": self._claude_opus,
                "quality": 1.0,
                "cost_per_1k": 15.0
            },
            {
                "name": "Gemini 3 Pro",
                "handler": self._gemini_pro,
                "quality": 0.9,
                "cost_per_1k": 1.25
            },
            {
                "name": "Gemini Flash",
                "handler": self._gemini_flash,
                "quality": 0.75,
                "cost_per_1k": 0.075
            },
            {
                "name": "Cached Response",
                "handler": self._cached_response,
                "quality": 0.5,
                "cost_per_1k": 0.0
            }
        ]

    async def execute(self, request: dict) -> dict:
        """Execute with graceful degradation."""
        errors = []

        for option in self.fallback_chain:
            try:
                result = await option["handler"](request)
                return {
                    "result": result,
                    "provider": option["name"],
                    "quality": option["quality"],
                    "degraded": option != self.fallback_chain[0]
                }
            except Exception as e:
                errors.append({
                    "provider": option["name"],
                    "error": str(e)
                })
                continue

        # All fallbacks failed
        raise AllFallbacksFailedError(errors)
```

---

## 5. API Quota Management

### 5.1 Quota Tracking

```python
from datetime import datetime, timedelta
from collections import defaultdict

class QuotaManager:
    """
    Track and enforce API quotas across providers.
    """

    def __init__(self):
        self.quotas = {
            "claude": {
                "daily_limit": 1_000_000,  # tokens
                "per_minute_limit": 10_000,
                "per_request_max": 100_000
            },
            "gemini": {
                "daily_limit": 10_000_000,
                "per_minute_limit": 100_000,
                "per_request_max": 1_000_000
            }
        }

        self.usage = defaultdict(lambda: {
            "daily": 0,
            "minute": 0,
            "daily_reset": datetime.now(),
            "minute_reset": datetime.now()
        })

    def _reset_if_needed(self, provider: str):
        """Reset counters if time window passed."""
        usage = self.usage[provider]
        now = datetime.now()

        if now - usage["daily_reset"] >= timedelta(days=1):
            usage["daily"] = 0
            usage["daily_reset"] = now

        if now - usage["minute_reset"] >= timedelta(minutes=1):
            usage["minute"] = 0
            usage["minute_reset"] = now

    def can_proceed(self, provider: str, estimated_tokens: int) -> tuple[bool, str]:
        """Check if request can proceed given quotas."""
        self._reset_if_needed(provider)

        quota = self.quotas[provider]
        usage = self.usage[provider]

        if estimated_tokens > quota["per_request_max"]:
            return False, f"Request too large: {estimated_tokens} > {quota['per_request_max']}"

        if usage["daily"] + estimated_tokens > quota["daily_limit"]:
            return False, f"Daily quota exceeded: {usage['daily']}/{quota['daily_limit']}"

        if usage["minute"] + estimated_tokens > quota["per_minute_limit"]:
            return False, f"Rate limit exceeded: {usage['minute']}/{quota['per_minute_limit']}/min"

        return True, "OK"

    def record_usage(self, provider: str, actual_tokens: int):
        """Record actual token usage."""
        self._reset_if_needed(provider)

        self.usage[provider]["daily"] += actual_tokens
        self.usage[provider]["minute"] += actual_tokens

    def get_remaining(self, provider: str) -> dict:
        """Get remaining quota for provider."""
        self._reset_if_needed(provider)

        quota = self.quotas[provider]
        usage = self.usage[provider]

        return {
            "daily_remaining": quota["daily_limit"] - usage["daily"],
            "daily_percent": (quota["daily_limit"] - usage["daily"]) / quota["daily_limit"],
            "minute_remaining": quota["per_minute_limit"] - usage["minute"]
        }
```

### 5.2 Intelligent Routing Based on Quotas

```python
class QuotaAwareRouter:
    """
    Route requests to optimal provider based on quotas and cost.
    """

    def __init__(self, quota_manager: QuotaManager):
        self.quota_manager = quota_manager

        self.providers = {
            "claude": {"quality": 1.0, "cost_per_1k": 15.0},
            "gemini": {"quality": 0.9, "cost_per_1k": 1.25},
            "gemini_flash": {"quality": 0.75, "cost_per_1k": 0.075}
        }

    def route(
        self,
        estimated_tokens: int,
        min_quality: float = 0.7,
        prefer: str = "cost"
    ) -> str:
        """
        Route to optimal provider.

        Args:
            estimated_tokens: Expected token usage
            min_quality: Minimum acceptable quality score
            prefer: "cost" or "quality"

        Returns:
            Provider name
        """
        available = []

        for provider, config in self.providers.items():
            if config["quality"] < min_quality:
                continue

            can_proceed, _ = self.quota_manager.can_proceed(provider, estimated_tokens)
            if not can_proceed:
                continue

            available.append((provider, config))

        if not available:
            raise NoAvailableProviderError("All providers at quota limit")

        if prefer == "cost":
            # Sort by cost (ascending)
            available.sort(key=lambda x: x[1]["cost_per_1k"])
        else:
            # Sort by quality (descending)
            available.sort(key=lambda x: x[1]["quality"], reverse=True)

        return available[0][0]
```

---

## 6. Backup & Disaster Recovery

### 6.1 KG Snapshot Strategy

```python
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

class KGBackupManager:
    """
    Manage knowledge graph backups with point-in-time recovery.
    """

    def __init__(self, db_path: str, backup_dir: str):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, tag: str = None) -> Path:
        """
        Create a point-in-time snapshot.

        Uses SQLite's backup API for consistency.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag_suffix = f"_{tag}" if tag else ""
        backup_name = f"kg_snapshot_{timestamp}{tag_suffix}.db"
        backup_path = self.backup_dir / backup_name

        # Use SQLite backup API
        source = sqlite3.connect(str(self.db_path))
        dest = sqlite3.connect(str(backup_path))

        with dest:
            source.backup(dest)

        source.close()
        dest.close()

        return backup_path

    def restore_snapshot(self, snapshot_path: Path):
        """Restore from a snapshot."""
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

        # Create safety backup of current state
        self.create_snapshot(tag="pre_restore")

        # Restore
        shutil.copy(snapshot_path, self.db_path)

    def list_snapshots(self) -> list:
        """List available snapshots."""
        snapshots = []
        for path in self.backup_dir.glob("kg_snapshot_*.db"):
            stat = path.stat()
            snapshots.append({
                "path": path,
                "name": path.name,
                "size_mb": stat.st_size / (1024 * 1024),
                "created": datetime.fromtimestamp(stat.st_mtime)
            })
        return sorted(snapshots, key=lambda x: x["created"], reverse=True)

    def cleanup_old_snapshots(self, keep_count: int = 10):
        """Remove old snapshots, keeping most recent."""
        snapshots = self.list_snapshots()

        for snapshot in snapshots[keep_count:]:
            snapshot["path"].unlink()
```

### 6.2 Embedding Cache Backup

```python
import pickle
import hashlib

class EmbeddingBackupManager:
    """
    Manage embedding cache backups.
    """

    def __init__(self, embedding_path: str, backup_dir: str):
        self.embedding_path = Path(embedding_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> Path:
        """Create backup of embeddings."""
        if not self.embedding_path.exists():
            raise FileNotFoundError("Embeddings file not found")

        # Calculate hash for deduplication
        with open(self.embedding_path, 'rb') as f:
            content_hash = hashlib.md5(f.read()).hexdigest()[:8]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"embeddings_{timestamp}_{content_hash}.pkl"
        backup_path = self.backup_dir / backup_name

        shutil.copy(self.embedding_path, backup_path)

        return backup_path

    def restore_backup(self, backup_path: Path):
        """Restore embeddings from backup."""
        # Validate backup
        with open(backup_path, 'rb') as f:
            data = pickle.load(f)

        if 'node_embeddings' not in data:
            raise ValueError("Invalid embeddings backup")

        shutil.copy(backup_path, self.embedding_path)
```

---

## 7. Performance Tuning

### 7.1 Connection Pooling

```python
from contextlib import contextmanager
from queue import Queue
from threading import Lock

class ConnectionPool:
    """
    Connection pool for SQLite databases.
    """

    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.lock = Lock()

        # Pre-populate pool
        for _ in range(pool_size):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self.pool.put(conn)

    @contextmanager
    def get_connection(self):
        """Get connection from pool."""
        conn = self.pool.get()
        try:
            yield conn
        finally:
            self.pool.put(conn)

    def close_all(self):
        """Close all connections."""
        while not self.pool.empty():
            conn = self.pool.get_nowait()
            conn.close()
```

### 7.2 Query Caching

```python
from functools import lru_cache
import hashlib
import json

class QueryCache:
    """
    Cache query results with TTL.
    """

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 300):
        self.cache = {}
        self.maxsize = maxsize
        self.ttl = ttl_seconds

    def _make_key(self, query: str, params: dict) -> str:
        """Create cache key from query and params."""
        data = json.dumps({"q": query, "p": params}, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()

    def get(self, query: str, params: dict) -> tuple[bool, any]:
        """Get cached result if valid."""
        key = self._make_key(query, params)

        if key not in self.cache:
            return False, None

        entry = self.cache[key]
        if datetime.now() - entry["time"] > timedelta(seconds=self.ttl):
            del self.cache[key]
            return False, None

        return True, entry["result"]

    def set(self, query: str, params: dict, result: any):
        """Cache result."""
        key = self._make_key(query, params)

        # Evict oldest if full
        if len(self.cache) >= self.maxsize:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["time"])
            del self.cache[oldest_key]

        self.cache[key] = {
            "result": result,
            "time": datetime.now()
        }
```

---

## 8. Operational Runbooks

### 8.1 Incident Response

```markdown
## Runbook: High Error Rate Alert

**Trigger:** Error rate > 5% for 2+ minutes

**Steps:**
1. Check error logs for pattern
   ```bash
   tail -f /var/log/nlke/error.log | grep -E "(ERROR|CRITICAL)"
   ```

2. Identify affected component
   - KG database: Check connection, disk space
   - Embeddings: Check memory, file corruption
   - External API: Check quota, rate limits

3. Mitigation
   - If KG: Restart with read-only replica
   - If embeddings: Fall back to keyword-only search
   - If API: Trigger graceful degradation

4. Root cause analysis
   - Collect logs and metrics
   - Document timeline
   - Create post-incident report
```

### 8.2 Deployment Checklist

```markdown
## Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Performance benchmarks within SLA
- [ ] Rollback plan documented
- [ ] Monitoring dashboards updated
- [ ] On-call notified

## Deployment Steps

1. [ ] Create pre-deployment snapshot
2. [ ] Deploy to staging
3. [ ] Run smoke tests on staging
4. [ ] Deploy to production (progressive rollout)
5. [ ] Monitor error rate for 15 minutes
6. [ ] If issues: rollback immediately

## Post-Deployment

- [ ] Verify metrics are normal
- [ ] Update deployment log
- [ ] Clean up old deployments
```

---

## Related Playbooks

| Playbook | Relationship |
|----------|--------------|
| PB 1: Cost Optimization | Production cost monitoring |
| PB 3: Agent Development | Agent health checks |
| PB 8: Continuous Learning | Fact persistence backup |
| PB 10: MCP Server Development | Server deployment |
| PB 11: Session Handoff | Crash recovery |

---

## Key Insights

- **#234**: Observability Enables Recursive Improvement
- **#235**: Workflows as Declarative Intent
- **Production Reality**: Development patterns need infrastructure for reliability

---

**Playbook Version:** 1.0
**Last Updated:** November 27, 2025
**Methodology:** NLKE v3.0
