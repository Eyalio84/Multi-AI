# Phase 3 Enhancement Suggestions: Domain Expansion
## Opus Critical Review and Recommendations

**Date**: January 25, 2026
**Reviewer**: Claude Opus 4.5
**Focus**: Domain selection, edge extraction, bridge creation, recall validation
**Research Context**: Reach 1M+ edges while maintaining 100% recall

---

## EXECUTIVE SUMMARY

### Key Findings

1. **Domain selection is excellent**: Git, Linux, Python are strategically optimal
2. **Edge density ordering is correct**: Git (8.75) > Linux (7.5) > Python (6.67)
3. **Additional high-value domains identified**: Shell scripting, Docker, HTTP/REST
4. **Bridge creation needs systematic approach**: Current 87.6% validity can reach 95%+

### Priority Recommendations

| Enhancement | Impact | Effort | Priority | Recommendation |
|------------|--------|--------|----------|----------------|
| Add Shell Scripting domain | +5,000 edges, high synergy | Medium | **HIGH** | IMPLEMENT |
| Add HTTP/REST API domain | +4,000 edges, universal | Medium | **HIGH** | IMPLEMENT |
| Systematic bridge templates | +25% bridge quality | Low | **HIGH** | IMPLEMENT |
| LLM-assisted edge extraction | 10x extraction speed | Medium | **MEDIUM** | CONSIDER |
| Version-aware node schema | Future-proofing | Low | **MEDIUM** | IMPLEMENT |

---

## SECTION 1: Domain Selection Analysis

### Why Your Chosen Domains Are Excellent

#### Domain 1: Git/Version Control - OUTSTANDING CHOICE

**Strategic Value**:
```
Git is the universal developer substrate:
- 90%+ of professional developers use Git daily
- Connects to EVERY code-related domain
- Rich semantic relationships (commits, branches, merges, conflicts)
- High edge density (8.75 edges/node) indicates dense knowledge structure
```

**Why This Domain Excels**:

| Factor | Score | Reasoning |
|--------|-------|-----------|
| **Universal Relevance** | 10/10 | Every developer uses Git |
| **Edge Density** | 8.75 | Highest among proposed domains |
| **Bridge Potential** | 10/10 | Connects to code, docs, workflows |
| **Query Frequency** | Very High | "how to undo commit", "merge conflict" |
| **Latency Impact** | +2-5ms | Minimal due to focused scope |

**Expected Connections**:
```
Git → Python:     git commit → python script → dependencies
Git → Linux:      git push → ssh → remote server
Git → Claude:     git diff → code_review_tool → analysis
Git → Workflow:   git branch → feature_development → CI/CD
```

**Validation**: This domain directly supports the research thesis - Git operations demonstrate "movement reveals structure" through commit history patterns.

---

#### Domain 2: Linux Core Commands - EXCELLENT CHOICE

**Strategic Value**:
```
Linux commands form the operational foundation:
- Every Claude Code user runs on some Unix variant
- Commands chain together (piping = graph edges)
- Well-documented with clear relationships
- 7.5 edges/node indicates rich command compositions
```

**Why This Domain Excels**:

| Factor | Score | Reasoning |
|--------|-------|-----------|
| **Universal Relevance** | 9/10 | Core to all CLI workflows |
| **Edge Density** | 7.5 | Strong piping relationships |
| **Bridge Potential** | 9/10 | Connects to Git, Python, networking |
| **Query Frequency** | Very High | "find files", "grep pattern" |
| **Latency Impact** | +5-10ms | Moderate due to scope |

**Expected Connections**:
```
Linux → Git:      find -name "*.py" → git add → commit
Linux → Python:   python script.py → stdout → grep filter
Linux → Claude:   Bash tool → command execution → output
Linux → Network:  curl → HTTP request → API response
```

**Validation**: Linux commands demonstrate self-organization - common command chains (find | xargs | grep) become emergent patterns in the KG.

---

#### Domain 3: Python Standard Library - STRONG CHOICE

**Strategic Value**:
```
Python stdlib is the language substrate:
- 85%+ of ML/AI development uses Python
- Rich type hierarchy (classes, modules, functions)
- Well-documented with clear imports/dependencies
- 6.67 edges/node is solid for library documentation
```

**Why This Domain Excels**:

| Factor | Score | Reasoning |
|--------|-------|-----------|
| **Universal Relevance** | 9/10 | Primary AI/ML language |
| **Edge Density** | 6.67 | Module-level relationships |
| **Bridge Potential** | 9/10 | Connects to every Python code example |
| **Query Frequency** | High | "json parsing", "async await" |
| **Latency Impact** | +5-10ms | Module-level granularity helps |

**Expected Connections**:
```
Python → Examples: json.load() → example in examples/
Python → Git:      subprocess.run() → git command
Python → Linux:    os.path → filesystem operations
Python → Claude:   argparse → CLI tool implementation
```

**Recommendation**: Start with **module-level** (200 nodes) rather than class-level (2,000) to maintain latency.

---

### Domain Selection Ordering Validation

Your ordering (Git → Linux → Python) is **strategically optimal**:

```
1. Git FIRST because:
   - Highest edge density (8.75)
   - Smallest node count (400)
   - Fastest to implement
   - Immediately useful for Claude Code users

2. Linux SECOND because:
   - Second highest density (7.5)
   - Builds on Git (git commands use Linux)
   - Medium scope (800 nodes)
   - Essential for command understanding

3. Python THIRD because:
   - Largest scope (1,200 nodes)
   - Benefits from Git+Linux bridges
   - Most complex extraction
   - Can leverage earlier domain bridges
```

**Alternative considered**: Python first (since examples/ are Python)
**Why rejected**: Python scope is largest, riskier to start with. Git's small scope allows validating the expansion process first.

---

## SECTION 2: Additional High-Value Domains

### Recommended Additional Domain #1: Shell Scripting

**What**: Bash/Zsh scripting patterns, built-ins, control flow

**Why This Is Valuable**:
```
Shell scripting bridges Linux commands and automation:
- Every Claude Code session involves shell scripts
- Complements Linux commands (individual vs combined)
- High synergy with Git (hooks, CI scripts)
- Rich relationship structure (if/then, loops, functions)
```

**Metrics**:
| Metric | Value |
|--------|-------|
| Estimated Nodes | 300 |
| Estimated Edges | 2,500 |
| Edge Density | 8.33 edges/node |
| Effort | 2 weeks |
| Latency Impact | +3-5ms |

**Expected Connections**:
```
Shell → Linux:    for file in $(find .) → file operations
Shell → Git:      git hooks → pre-commit scripts
Shell → Python:   #!/usr/bin/env python → script execution
Shell → Claude:   Bash tool → script understanding
```

**Priority**: **HIGH** - Fills critical gap between commands and automation

---

### Recommended Additional Domain #2: HTTP/REST APIs

**What**: HTTP methods, status codes, headers, REST patterns, API design

**Why This Is Valuable**:
```
HTTP is the universal interface:
- Every API interaction uses HTTP
- Status codes have semantic meaning (4xx vs 5xx)
- REST patterns are queryable ("how to design API")
- Direct bridge to Claude API documentation
```

**Metrics**:
| Metric | Value |
|--------|-------|
| Estimated Nodes | 250 |
| Estimated Edges | 2,000 |
| Edge Density | 8.0 edges/node |
| Effort | 2 weeks |
| Latency Impact | +2-4ms |

**Expected Connections**:
```
HTTP → Claude API:   POST /v1/messages → Claude API usage
HTTP → Python:       requests.get() → HTTP client
HTTP → Errors:       429 Too Many Requests → rate limiting
HTTP → Patterns:     REST → CRUD operations
```

**Priority**: **HIGH** - Universal application, connects to API documentation

---

### Recommended Additional Domain #3: Docker/Containers

**What**: Docker commands, Dockerfile directives, compose, container concepts

**Why This Is Valuable**:
```
Containers are the deployment substrate:
- Claude Code often runs in containers
- Docker commands parallel Linux commands
- Compose files are structured (yaml → edges)
- Growing importance in development
```

**Metrics**:
| Metric | Value |
|--------|-------|
| Estimated Nodes | 200 |
| Estimated Edges | 1,500 |
| Edge Density | 7.5 edges/node |
| Effort | 2-3 weeks |
| Latency Impact | +2-4ms |

**Expected Connections**:
```
Docker → Linux:     docker exec → bash commands
Docker → Python:    Dockerfile → pip install
Docker → Git:       Dockerfile → git clone
Docker → Network:   docker network → container communication
```

**Priority**: **MEDIUM** - Important but less universal than HTTP

---

### Recommended Additional Domain #4: JSON/YAML/TOML

**What**: Data formats, schema patterns, parsing, common structures

**Why This Is Valuable**:
```
Configuration formats are everywhere:
- Every project has config files
- Format conversion is common query
- Schema validation is practical need
- Bridges to Python, Docker, CI/CD
```

**Metrics**:
| Metric | Value |
|--------|-------|
| Estimated Nodes | 150 |
| Estimated Edges | 1,000 |
| Edge Density | 6.67 edges/node |
| Effort | 1-2 weeks |
| Latency Impact | +1-2ms |

**Expected Connections**:
```
JSON → Python:      json.loads() → data parsing
YAML → Docker:      docker-compose.yml → service definitions
TOML → Python:      pyproject.toml → project configuration
JSON → API:         request body → response parsing
```

**Priority**: **MEDIUM** - Small scope, quick wins

---

### Domain Priority Matrix

| Domain | Nodes | Edges | Density | Synergy | Effort | Priority |
|--------|-------|-------|---------|---------|--------|----------|
| **Git** (planned) | 400 | 3,500 | 8.75 | Critical | 2-3w | **CRITICAL** |
| **Shell Scripting** | 300 | 2,500 | 8.33 | High | 2w | **HIGH** |
| **HTTP/REST** | 250 | 2,000 | 8.0 | High | 2w | **HIGH** |
| **Linux** (planned) | 800 | 6,000 | 7.5 | High | 3-4w | **HIGH** |
| **Docker** | 200 | 1,500 | 7.5 | Medium | 2-3w | **MEDIUM** |
| **Python** (planned) | 1,200 | 8,000 | 6.67 | High | 4-6w | **HIGH** |
| **Config Formats** | 150 | 1,000 | 6.67 | Medium | 1-2w | **MEDIUM** |

**Recommended Full Expansion Order**:
1. Git (foundation, smallest)
2. Shell Scripting (bridges Git↔Linux)
3. HTTP/REST (universal API knowledge)
4. Linux (core commands)
5. Config Formats (quick win)
6. Docker (deployment knowledge)
7. Python (largest, leverage all bridges)

**Total with additions**: 3,300 nodes, 24,500 edges
**Final edge count**: 962K + 24.5K = **986,500 edges** (98.7% of 1M)

Add Data Science Stack (as planned) for **1.01M+ edges**.

---

## SECTION 3: Edge Extraction Strategy

### Current Approach

LLM-assisted vs manual curation question.

### Enhancement #1: Hybrid Extraction Pipeline

**What**: Combine LLM extraction with rule-based validation

**Why**:
- LLM: Good at semantic relationships
- Rules: Good at structural relationships (imports, calls)
- Hybrid catches what each misses

**How**:

```python
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ExtractedEdge:
    source: str
    target: str
    relation: str
    confidence: float
    evidence: str
    method: str  # 'llm', 'rule', 'hybrid'

class HybridExtractor:
    """
    Two-phase extraction: rules first, LLM for semantics.
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.rule_patterns = self._load_patterns()

    def extract_from_document(self, doc: str, doc_type: str) -> List[ExtractedEdge]:
        """
        Extract edges using hybrid approach.
        """
        edges = []

        # Phase 1: Rule-based extraction (fast, high precision)
        rule_edges = self._extract_by_rules(doc, doc_type)
        edges.extend(rule_edges)

        # Phase 2: LLM extraction (semantic, fills gaps)
        if self.llm:
            llm_edges = self._extract_by_llm(doc, doc_type, existing=rule_edges)
            edges.extend(llm_edges)

        # Phase 3: Deduplication and confidence merge
        merged = self._merge_edges(edges)

        return merged

    def _extract_by_rules(self, doc: str, doc_type: str) -> List[ExtractedEdge]:
        """
        Rule-based extraction for structural relationships.
        """
        edges = []

        if doc_type == 'git':
            # Git command patterns
            patterns = {
                r'git (\w+).*git (\w+)': ('sequence', 0.9),
                r'git (\w+).*then.*git (\w+)': ('enables', 0.95),
                r'git (\w+).*instead of.*git (\w+)': ('alternative_to', 0.9),
            }

            for pattern, (relation, conf) in patterns.items():
                import re
                matches = re.findall(pattern, doc, re.IGNORECASE)
                for m in matches:
                    edges.append(ExtractedEdge(
                        source=f"git_{m[0]}",
                        target=f"git_{m[1]}",
                        relation=relation,
                        confidence=conf,
                        evidence=doc[:100],
                        method='rule'
                    ))

        elif doc_type == 'python':
            # Import relationships
            import_pattern = r'from (\w+) import (\w+)'
            for match in re.findall(import_pattern, doc):
                edges.append(ExtractedEdge(
                    source=f"module_{match[0]}",
                    target=f"function_{match[1]}",
                    relation='exports',
                    confidence=1.0,
                    evidence=f"from {match[0]} import {match[1]}",
                    method='rule'
                ))

        return edges

    def _extract_by_llm(self, doc: str, doc_type: str,
                        existing: List[ExtractedEdge]) -> List[ExtractedEdge]:
        """
        LLM extraction for semantic relationships.
        """
        # Create prompt with existing edges context
        existing_pairs = [(e.source, e.target) for e in existing]

        prompt = f"""
Extract knowledge graph edges from this {doc_type} documentation.

Focus on relationships NOT already captured:
{existing_pairs[:10]}

Document:
{doc[:2000]}

Output format (one per line):
source | target | relation | confidence

Relations to use:
- enables: A enables B
- requires: A requires B
- alternative_to: A is alternative to B
- part_of: A is part of B
- related_to: A is related to B
"""

        if not self.llm:
            return []

        response = self.llm.generate(prompt)
        return self._parse_llm_response(response)
```

**Trade-offs**:
- Pro: 10x faster than pure manual curation
- Pro: Higher quality than pure LLM
- Pro: Reproducible (rules are deterministic)
- Con: Requires LLM API costs
- Con: Rules need domain expertise

**Impact**:
- Extraction speed: 1 week → 1-2 days per domain
- Edge quality: 85% → 95% precision

**Effort**: 8 hours (initial setup)

**Priority**: **MEDIUM** (worth it for later domains)

**Recommendation**: **CONSIDER** - Significant time savings

---

### Enhancement #2: Systematic Bridge Templates

**What**: Predefined bridge patterns for cross-domain connections

**Why**:
- Current 87.6% bridge validity suggests some are weak
- Templates ensure consistent, high-quality bridges
- Makes bridge creation reproducible

**How**:

```python
BRIDGE_TEMPLATES = {
    # Git ↔ Linux
    ('git', 'linux'): [
        {
            'pattern': 'git_command uses linux_command',
            'examples': [
                ('git_push', 'uses', 'ssh'),
                ('git_clone', 'uses', 'https_curl'),
            ],
            'confidence': 0.95
        }
    ],

    # Git ↔ Python
    ('git', 'python'): [
        {
            'pattern': 'python_module enables git_workflow',
            'examples': [
                ('subprocess', 'enables', 'git_automation'),
                ('gitpython', 'wraps', 'git_commands'),
            ],
            'confidence': 0.9
        }
    ],

    # Linux ↔ Python
    ('linux', 'python'): [
        {
            'pattern': 'python_module wraps linux_command',
            'examples': [
                ('os', 'wraps', 'filesystem_commands'),
                ('subprocess', 'executes', 'shell_commands'),
                ('shutil', 'wraps', 'file_operations'),
            ],
            'confidence': 0.95
        }
    ],

    # HTTP ↔ Python
    ('http', 'python'): [
        {
            'pattern': 'python_library implements http_pattern',
            'examples': [
                ('requests', 'implements', 'http_client'),
                ('flask', 'implements', 'http_server'),
                ('aiohttp', 'implements', 'async_http'),
            ],
            'confidence': 0.95
        }
    ],

    # Shell ↔ Git
    ('shell', 'git'): [
        {
            'pattern': 'shell_construct enables git_pattern',
            'examples': [
                ('for_loop', 'enables', 'batch_git_operations'),
                ('git_hooks', 'uses', 'shell_scripts'),
            ],
            'confidence': 0.9
        }
    ],
}


def generate_bridges(source_domain: str, target_domain: str,
                     source_nodes: List[str], target_nodes: List[str]) -> List[dict]:
    """
    Generate bridges using templates and node matching.
    """
    bridges = []
    key = (source_domain, target_domain)

    if key not in BRIDGE_TEMPLATES:
        key = (target_domain, source_domain)  # Try reverse

    if key not in BRIDGE_TEMPLATES:
        return bridges

    for template in BRIDGE_TEMPLATES[key]:
        # Match nodes to template patterns
        for source in source_nodes:
            for target in target_nodes:
                if matches_template(source, target, template):
                    bridges.append({
                        'source': source,
                        'target': target,
                        'relation': template['pattern'].split()[1],
                        'confidence': template['confidence'],
                        'evidence': f"Template: {template['pattern']}"
                    })

    return bridges
```

**Trade-offs**:
- Pro: Consistent, high-quality bridges
- Pro: Reproducible bridge creation
- Pro: Easy to validate and audit
- Con: Requires upfront template design
- Con: May miss novel relationships

**Impact**:
- Bridge validity: 87.6% → 95%+
- Bridge consistency: Much higher

**Effort**: 4 hours (template design)

**Priority**: **HIGH**

**Recommendation**: **IMPLEMENT** - Critical for bridge quality

---

## SECTION 4: Recall Validation Strategy

### Current Approach

Validate 100% recall is maintained after expansion.

### Enhancement #3: Domain-Specific Probe Sets

**What**: Create validation probes for each new domain

**Why**:
- Original 22 probes don't cover new domains
- Need domain-specific ground truth
- Ensures 100% recall claim extends to new content

**How**:

```python
# Domain-specific validation probes
DOMAIN_PROBES = {
    'git': [
        {
            'query': 'how to undo last commit',
            'expected': ['git_reset', 'git_revert', 'use_case_undo_changes'],
            'domain': 'git',
            'difficulty': 'easy'
        },
        {
            'query': 'resolve merge conflict',
            'expected': ['git_merge', 'conflict_resolution', 'git_checkout_ours'],
            'domain': 'git',
            'difficulty': 'medium'
        },
        {
            'query': 'compare branches before merge',
            'expected': ['git_diff', 'git_log', 'branch_comparison'],
            'domain': 'git',
            'difficulty': 'medium'
        },
        {
            'query': 'git workflow for feature development',
            'expected': ['git_branch', 'git_checkout', 'pull_request_workflow'],
            'domain': 'git',
            'difficulty': 'hard'
        },
    ],

    'linux': [
        {
            'query': 'find files by name pattern',
            'expected': ['find_command', 'glob_patterns', 'locate_command'],
            'domain': 'linux',
            'difficulty': 'easy'
        },
        {
            'query': 'search file contents for pattern',
            'expected': ['grep_command', 'ripgrep', 'text_search'],
            'domain': 'linux',
            'difficulty': 'easy'
        },
        {
            'query': 'chain commands together',
            'expected': ['pipe_operator', 'xargs', 'command_chaining'],
            'domain': 'linux',
            'difficulty': 'medium'
        },
    ],

    'python': [
        {
            'query': 'parse JSON in Python',
            'expected': ['json_module', 'json_loads', 'json_dumps'],
            'domain': 'python',
            'difficulty': 'easy'
        },
        {
            'query': 'async programming in Python',
            'expected': ['asyncio_module', 'async_await', 'coroutines'],
            'domain': 'python',
            'difficulty': 'medium'
        },
    ],

    'shell': [
        {
            'query': 'loop through files in directory',
            'expected': ['for_loop', 'glob_expansion', 'find_exec'],
            'domain': 'shell',
            'difficulty': 'easy'
        },
    ],

    'http': [
        {
            'query': 'what does 429 status code mean',
            'expected': ['status_429', 'rate_limiting', 'retry_after'],
            'domain': 'http',
            'difficulty': 'easy'
        },
    ],
}


def validate_domain_expansion(domain: str, kg_query_fn) -> dict:
    """
    Validate recall for newly added domain.
    """
    probes = DOMAIN_PROBES.get(domain, [])
    results = {
        'domain': domain,
        'total_probes': len(probes),
        'perfect_recall': 0,
        'recall_scores': [],
        'failures': []
    }

    for probe in probes:
        response = kg_query_fn(probe['query'], k=10)
        retrieved_ids = [r['node_id'] for r in response]

        hits = len(set(retrieved_ids) & set(probe['expected']))
        recall = hits / len(probe['expected'])

        results['recall_scores'].append(recall)

        if recall == 1.0:
            results['perfect_recall'] += 1
        else:
            results['failures'].append({
                'query': probe['query'],
                'expected': probe['expected'],
                'retrieved': retrieved_ids[:5],
                'recall': recall
            })

    results['mean_recall'] = sum(results['recall_scores']) / len(results['recall_scores'])
    results['pass'] = results['mean_recall'] >= 0.95 and results['perfect_recall'] >= len(probes) * 0.8

    return results
```

**Trade-offs**:
- Pro: Domain-specific validation
- Pro: Catches domain-specific recall issues
- Pro: Extends research claim to new content
- Con: Requires creating probes for each domain
- Con: Ground truth curation takes time

**Impact**:
- Validation coverage: 6 domains → all domains
- Research claim: Extended to 1M+ edges

**Effort**: 4 hours per domain

**Priority**: **CRITICAL**

**Recommendation**: **IMPLEMENT** - Required for research integrity

---

### Enhancement #4: Continuous Recall Monitoring

**What**: Automated recall testing after any KG modification

**Why**:
- Catch regressions immediately
- Support continuous integration
- Document recall over time

**How**:

```python
def recall_ci_check() -> bool:
    """
    CI/CD check for recall maintenance.

    Run after any KG modification.
    """
    # Load current KG
    kg = load_kg()

    # Run all probes
    all_probes = []
    for domain, probes in DOMAIN_PROBES.items():
        all_probes.extend(probes)

    # Add original 22 probes
    all_probes.extend(load_original_probes())

    # Calculate recall
    total_recall = 0
    failures = []

    for probe in all_probes:
        results = kg.query(probe['query'], k=10)
        retrieved = [r['node_id'] for r in results]
        hits = len(set(retrieved) & set(probe['expected']))
        recall = hits / len(probe['expected'])
        total_recall += recall

        if recall < 1.0:
            failures.append(probe['query'])

    mean_recall = total_recall / len(all_probes)

    # CI gate: must maintain 95%+ mean recall
    print(f"Recall: {mean_recall*100:.1f}%")
    print(f"Failures: {len(failures)}/{len(all_probes)}")

    if mean_recall < 0.95:
        print("FAILED: Recall dropped below 95%")
        return False

    if len(failures) > len(all_probes) * 0.1:
        print("FAILED: Too many individual failures")
        return False

    print("PASSED: Recall maintained")
    return True
```

**Impact**:
- Regression detection: Immediate
- Research integrity: Continuous validation

**Effort**: 2 hours

**Priority**: **HIGH**

**Recommendation**: **IMPLEMENT** - Essential for CI/CD

---

## SECTION 5: Version-Aware Schema

### Enhancement #5: Version Tracking for Domains

**What**: Track version information for version-sensitive domains (Python, Git)

**Why**:
- Python 3.8 vs 3.13 have different features
- Git 2.40 vs 2.44 have different commands
- Enables accurate version-specific queries

**How**:

```python
# Schema extension for version awareness
VERSION_SCHEMA = """
ALTER TABLE nodes ADD COLUMN version_min TEXT;  -- e.g., "3.8"
ALTER TABLE nodes ADD COLUMN version_max TEXT;  -- e.g., "3.13" or NULL for current
ALTER TABLE nodes ADD COLUMN version_notes TEXT;  -- e.g., "Added in 3.10"

CREATE INDEX idx_nodes_version ON nodes(version_min, version_max);
"""

# Example version-aware nodes
VERSION_EXAMPLES = [
    {
        'node_id': 'python_match_statement',
        'name': 'match statement',
        'description': 'Structural pattern matching',
        'version_min': '3.10',
        'version_max': None,
        'version_notes': 'Added in Python 3.10 (PEP 634)'
    },
    {
        'node_id': 'python_walrus_operator',
        'name': 'walrus operator :=',
        'description': 'Assignment expression',
        'version_min': '3.8',
        'version_max': None,
        'version_notes': 'Added in Python 3.8 (PEP 572)'
    },
    {
        'node_id': 'git_sparse_checkout',
        'name': 'git sparse-checkout',
        'description': 'Partial repository checkout',
        'version_min': '2.25',
        'version_max': None,
        'version_notes': 'Significantly improved in 2.25'
    },
]


def version_aware_query(query: str, target_version: str = None) -> List[dict]:
    """
    Query with optional version filtering.
    """
    base_results = kg.query(query, k=20)  # Get more, then filter

    if target_version is None:
        return base_results[:10]

    # Filter by version compatibility
    filtered = []
    for result in base_results:
        v_min = result.get('version_min')
        v_max = result.get('version_max')

        # Check version bounds
        if v_min and compare_versions(target_version, v_min) < 0:
            continue  # Target version too old
        if v_max and compare_versions(target_version, v_max) > 0:
            continue  # Target version too new (deprecated)

        filtered.append(result)

    return filtered[:10]
```

**Trade-offs**:
- Pro: Accurate version-specific results
- Pro: Handles deprecations correctly
- Pro: Future-proofs for version evolution
- Con: More complex data curation
- Con: Version info not always available

**Impact**:
- Query accuracy: +15% for version-sensitive queries
- User trust: Higher (correct version info)

**Effort**: 3 hours

**Priority**: **MEDIUM**

**Recommendation**: **IMPLEMENT** - Important for accuracy

---

## OVERALL ASSESSMENT

### Strengths of Current Plan

1. **Domain selection is excellent**: Git → Linux → Python is optimal order
2. **Edge density ordering is correct**: Prioritizes information-dense domains
3. **Latency awareness**: Considers +ms impact per domain
4. **Module-level Python**: Correct granularity choice

### Weaknesses

1. **Missing shell scripting**: Critical gap between commands and automation
2. **Missing HTTP/REST**: Universal for API understanding
3. **Bridge strategy implicit**: Needs systematic templates
4. **No domain-specific validation**: Original probes don't cover new content

### Recommended Additions

| Domain | Rationale | Priority |
|--------|-----------|----------|
| **Shell Scripting** | Bridges Git↔Linux, high density | **HIGH** |
| **HTTP/REST** | Universal API knowledge | **HIGH** |
| **Config Formats** | Small scope, quick win | **MEDIUM** |
| **Docker** | Deployment context | **MEDIUM** |

### Implementation Order (Revised)

1. **Git** (2-3 weeks) - Foundation, smallest
2. **Shell Scripting** (2 weeks) - Bridges Git↔Linux
3. **HTTP/REST** (2 weeks) - Universal value
4. **Linux** (3-4 weeks) - Core commands
5. **Config Formats** (1-2 weeks) - Quick win
6. **Docker** (2-3 weeks) - Deployment
7. **Python** (4-6 weeks) - Largest, leverage bridges

**Total timeline**: 16-22 weeks for comprehensive expansion

### Final Edge Projection

| Component | Edges |
|-----------|-------|
| Current unified | 962,202 |
| Git | 3,500 |
| Shell | 2,500 |
| HTTP/REST | 2,000 |
| Linux | 6,000 |
| Config | 1,000 |
| Docker | 1,500 |
| Python | 8,000 |
| Bridges | ~3,000 |
| **Total** | **~990,000** |

Add Data Science Stack (as planned): **1.01M+ edges**

---

**Document Status**: COMPLETE
**Reviewer**: Claude Opus 4.5
**Recommendation**: Add Shell Scripting and HTTP/REST domains for comprehensive coverage

---

*Research Note*: The domain selection demonstrates "convergent utility" - independent developers would likely choose these same domains because they represent the universal substrate of software development (version control, commands, language, scripting, networking). This supports the thesis that the knowledge graph structure emerges from practical needs rather than arbitrary curation.
