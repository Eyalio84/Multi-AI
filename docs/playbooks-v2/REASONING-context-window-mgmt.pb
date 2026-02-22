# PLAYBOOK-9: Context Window Management

> **Synthesis Origin**: Claude Code Documentation + Prompt Caching + Session Patterns
> **Color Mix**: Blue (Context Architecture) + Yellow (Cost Optimization) = Green (Efficient Sessions)

## Overview

This playbook covers **strategic management of Claude's 200K context window** for maximum efficiency. Master the CLAUDE.md hierarchy, session lifecycle commands, and cost-optimized context placement.

**Key Insight**: Context placement directly affects both **prompt caching** (cost) and **attention patterns** (quality). Strategic organization can achieve 90%+ cache hit rates while improving response quality.

### Strategic Value

| Strategy | Token Impact | Cost Impact | Quality Impact |
|----------|-------------|-------------|----------------|
| Random context | Baseline | Baseline | Baseline |
| CLAUDE.md hierarchy | -20% | -40% (caching) | +15% (consistency) |
| Session management | -50% | -60% | +10% (focus) |
| Full optimization | -60% | -90% | +25% |

---

## Part 1: CLAUDE.md Hierarchy

### 1.1 File Discovery Order

Claude Code reads CLAUDE.md files in a specific order, building cumulative context:

```
┌─────────────────────────────────────────────────────────────┐
│              CLAUDE.MD DISCOVERY HIERARCHY                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. ~/.claude/CLAUDE.md              ← Global defaults       │
│         │                               (all projects)       │
│         ▼                                                    │
│  2. ~/projects/CLAUDE.md             ← Organization level    │
│         │                               (shared patterns)    │
│         ▼                                                    │
│  3. ~/projects/myapp/CLAUDE.md       ← Project root          │
│         │                               (project-specific)   │
│         ▼                                                    │
│  4. ~/projects/myapp/src/CLAUDE.md   ← Subdirectory          │
│         │                               (module-specific)    │
│         ▼                                                    │
│  5. .claude/settings.json            ← Local overrides       │
│                                         (user preferences)   │
│                                                              │
│  Each level INHERITS from parent and can OVERRIDE settings   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Content Organization Strategy

**Global CLAUDE.md** (`~/.claude/CLAUDE.md`):
```markdown
# Global Preferences

## Code Style
- Use 4-space indentation
- Prefer explicit over implicit
- Include type hints in Python

## Communication
- Be concise, avoid redundant explanations
- Use code blocks with language tags
- Format file paths as `path/to/file.py:line`

## Safety
- Never commit secrets or credentials
- Always validate user input
- Use parameterized queries for SQL
```

**Project CLAUDE.md** (project root):
```markdown
# Project: MyApp

## Architecture
This is a FastAPI + React application with PostgreSQL.

## Commands
- `npm run dev` - Start frontend dev server
- `uvicorn main:app --reload` - Start backend
- `pytest` - Run tests

## Conventions
- API routes in `src/api/`
- React components in `frontend/src/components/`
- Database models in `src/models/`

## Critical Files
- `src/config.py` - Environment configuration
- `src/auth/` - Authentication (security-sensitive)
```

**Module CLAUDE.md** (subdirectory):
```markdown
# Module: Authentication

## Security Requirements
- All passwords hashed with bcrypt
- JWT tokens expire in 1 hour
- Rate limit: 5 failed attempts triggers lockout

## Testing
- Integration tests require test database
- Run `pytest src/auth/ -v` for auth tests only

## Dependencies
This module depends on:
- `src/models/user.py`
- `src/utils/crypto.py`
```

### 1.3 Caching-Optimized Structure

Structure your CLAUDE.md for **maximum cache hit rate**:

```markdown
# Project Instructions

<!--
  CACHING STRATEGY:
  - First 1024+ tokens = always cached (system layer)
  - Put stable content first
  - Put volatile content last
-->

## [STABLE] Architecture Overview
<!-- This rarely changes - ideal for caching -->
This is a Python 3.11 project using:
- FastAPI for REST API
- SQLAlchemy for ORM
- Celery for background tasks
- Redis for caching
- PostgreSQL for persistence

The codebase follows hexagonal architecture:
- `src/domain/` - Business logic (no framework dependencies)
- `src/adapters/` - External integrations
- `src/api/` - FastAPI routes
- `src/infrastructure/` - Database, cache implementations

## [STABLE] Code Standards
<!-- Also rarely changes -->
- Type hints required for all functions
- Docstrings in Google format
- 100% test coverage for domain layer
- Max function length: 50 lines

## [SEMI-STABLE] Current Sprint Focus
<!-- Changes weekly -->
Working on user authentication refactor.
Key files: `src/auth/*.py`

## [VOLATILE] Recent Changes
<!-- Changes frequently - put last -->
- 2024-01-15: Added rate limiting
- 2024-01-14: Fixed JWT refresh bug
```

---

## Part 2: Session Lifecycle Management

### 2.1 Session Commands

| Command | Effect | Use When |
|---------|--------|----------|
| `/clear` | Reset conversation completely | Starting new task |
| `/compact` | Summarize and compress history | Mid-session cleanup |
| `/resume` | Resume previous session | Continue complex work |
| `/memory` | View memory statistics | Debugging context issues |

### 2.2 When to Clear vs Compact

```
┌─────────────────────────────────────────────────────────────┐
│                  SESSION MANAGEMENT DECISION                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                    Is context relevant?                      │
│                           │                                  │
│              ┌────────────┴────────────┐                    │
│              │                         │                     │
│              ▼                         ▼                     │
│        YES (>50%)                 NO (<50%)                 │
│              │                         │                     │
│     Use /compact                 Use /clear                  │
│     ─────────────                ──────────                  │
│     • Preserves key              • Fresh start               │
│       decisions                  • No stale context          │
│     • Maintains thread           • Best for new task         │
│     • Good for ongoing           • Resets all state          │
│       complex task                                           │
│                                                              │
│  Token Usage:                                                │
│  ─────────────                                               │
│  /clear   → 0 tokens carried forward                        │
│  /compact → ~2000-5000 tokens (summary)                     │
│  Nothing  → Full history (~50K+ tokens possible)            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Session Resume Pattern

For long-running tasks, create explicit checkpoints:

```markdown
<!-- Save to .claude/session_checkpoint.md -->
# Session Checkpoint: Auth Refactor

## Completed
- [x] Extracted JWT logic to `src/auth/jwt.py`
- [x] Created `TokenService` class
- [x] Added unit tests for token generation

## In Progress
- [ ] Integrate TokenService with login endpoint
- [ ] Update refresh token flow

## Key Decisions Made
1. Using RS256 for JWT signing (asymmetric)
2. Access tokens: 15 min, Refresh tokens: 7 days
3. Storing refresh tokens in Redis, not database

## Files Modified
- `src/auth/jwt.py` (new)
- `src/auth/service.py` (refactored)
- `tests/auth/test_jwt.py` (new)

## Next Session
Start with: "Continue auth refactor from checkpoint"
```

Then in new session:
```
/clear
Read .claude/session_checkpoint.md and continue the auth refactor.
```

---

## Part 3: Context Budget Optimization

### 3.1 Token Budget Categories

```
┌─────────────────────────────────────────────────────────────┐
│              200K CONTEXT BUDGET ALLOCATION                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ SYSTEM LAYER (10-15K tokens)              CACHED    │    │
│  │ • CLAUDE.md instructions                            │    │
│  │ • Tool definitions                                  │    │
│  │ • Safety guidelines                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ CONTEXT LAYER (20-50K tokens)            SEMI-CACHED│    │
│  │ • Relevant file contents                            │    │
│  │ • Documentation snippets                            │    │
│  │ • Test results                                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ CONVERSATION LAYER (50-100K tokens)      DYNAMIC    │    │
│  │ • User messages                                     │    │
│  │ • Assistant responses                               │    │
│  │ • Tool outputs                                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ RESERVE (30-50K tokens)                  OVERFLOW   │    │
│  │ • Large file reads                                  │    │
│  │ • Complex tool outputs                              │    │
│  │ • Extended thinking                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 File Reading Strategy

**Anti-Pattern**: Reading entire files

```python
# BAD: Loads 5000+ line file into context
Read entire src/api/routes.py
```

**Pattern**: Targeted reading with line ranges

```python
# GOOD: Only load relevant section
Read src/api/routes.py lines 150-200  # Just the auth routes
```

**Pattern**: Use grep before read

```bash
# Find exactly where to look
Grep "def login" in src/api/*.py

# Then read only that function
Read src/api/auth.py lines 45-80
```

### 3.3 Context Injection via Custom Commands

Create focused context commands in `.claude/commands/`:

```markdown
<!-- .claude/commands/auth-context.md -->
# Load Authentication Context

Read and summarize these files for auth work:
- src/auth/service.py (core logic)
- src/auth/jwt.py (token handling)
- src/models/user.py (user model)
- tests/auth/conftest.py (test fixtures)

Focus on:
- Current authentication flow
- Token generation/validation
- User session management
```

Usage:
```
/auth-context
Now help me add OAuth support
```

---

## Part 4: Memory and Persistence

### 4.1 Memory Types in Claude Code

| Memory Type | Scope | Persistence | Location |
|-------------|-------|-------------|----------|
| Session memory | Current chat | Until /clear | In-memory |
| Project memory | Per project | Across sessions | `.claude/memory/` |
| User memory | All projects | Permanent | `~/.claude/memory/` |

### 4.2 Explicit Memory Management

**Creating persistent memory**:

```markdown
<!-- .claude/memory/architecture.md -->
# Architecture Decisions

## Database
- PostgreSQL 15 for main storage
- Redis for session cache
- Decision date: 2024-01-01
- Rationale: Need ACID compliance + JSON support

## API Design
- REST for CRUD operations
- WebSocket for real-time features
- Decision date: 2024-01-05
- Rationale: REST is simpler for most operations

## Authentication
- JWT with RS256 signing
- Decision date: 2024-01-10
- Rationale: Asymmetric keys allow service-to-service verification
```

**Referencing memory**:

```
Considering the architecture decisions in memory,
should we add GraphQL or stick with REST?
```

### 4.3 Session Summary Pattern

At the end of complex sessions, request a summary:

```
Please summarize this session:
1. What we accomplished
2. Key decisions made
3. Outstanding issues
4. Recommended next steps

Format for saving to .claude/memory/session_YYYYMMDD.md
```

---

## Part 5: Cost-Optimized Context Patterns

### 5.1 Cache-First Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              CACHE-FIRST CONTEXT ARCHITECTURE                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  REQUEST FLOW:                                               │
│  ─────────────                                               │
│                                                              │
│  User Query                                                  │
│      │                                                       │
│      ▼                                                       │
│  ┌─────────────┐                                            │
│  │ Check Cache │ ←── Is this context already cached?        │
│  └──────┬──────┘                                            │
│         │                                                    │
│    ┌────┴────┐                                              │
│    │         │                                               │
│    ▼         ▼                                               │
│  HIT       MISS                                              │
│    │         │                                               │
│    │    ┌────┴────┐                                         │
│    │    │ Load &  │                                         │
│    │    │ Cache   │                                         │
│    │    └────┬────┘                                         │
│    │         │                                               │
│    └────┬────┘                                              │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐                                            │
│  │  Assemble   │                                            │
│  │   Context   │                                            │
│  └──────┬──────┘                                            │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐                                            │
│  │    Send     │                                            │
│  │  to Claude  │                                            │
│  └─────────────┘                                            │
│                                                              │
│  CACHING RULES:                                              │
│  ──────────────                                              │
│  • Minimum 1024 tokens to cache                             │
│  • Stable content first (maximizes prefix match)            │
│  • Cache expires at 5 minutes of inactivity                 │
│  • Same prefix = cache hit (90% cost reduction)             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Layered Context Template

Structure messages to maximize cache hits:

```python
# Context assembly order (most stable → least stable)
context_layers = [
    # Layer 1: System (always same) - CACHED
    system_prompt,           # ~2000 tokens
    tool_definitions,        # ~3000 tokens
    claude_md_content,       # ~2000 tokens

    # Layer 2: Project (changes rarely) - USUALLY CACHED
    project_architecture,    # ~1500 tokens
    coding_standards,        # ~500 tokens

    # Layer 3: Task (changes per task) - SOMETIMES CACHED
    relevant_file_contents,  # ~5000-20000 tokens
    test_results,            # ~1000 tokens

    # Layer 4: Conversation (always changes) - NEVER CACHED
    message_history,         # Variable
    current_query            # Variable
]
```

### 5.3 Token Counting Heuristics

Quick estimation without API calls:

```python
def estimate_tokens(text: str) -> int:
    """
    Estimate token count using heuristics.

    Rules of thumb:
    - English: ~4 characters per token
    - Code: ~3 characters per token (more symbols)
    - JSON: ~2.5 characters per token (high symbol density)
    """
    # Simple character-based estimation
    char_count = len(text)

    # Detect content type
    if text.strip().startswith('{') or text.strip().startswith('['):
        # JSON content
        return int(char_count / 2.5)
    elif any(kw in text for kw in ['def ', 'class ', 'function ', 'import ']):
        # Code content
        return int(char_count / 3)
    else:
        # English text
        return int(char_count / 4)


def check_budget(context_parts: list, budget: int = 150000) -> dict:
    """Check if context fits within budget."""
    total = sum(estimate_tokens(part) for part in context_parts)
    return {
        "total_tokens": total,
        "budget": budget,
        "remaining": budget - total,
        "utilization": f"{(total/budget)*100:.1f}%",
        "ok": total < budget
    }
```

---

## Part 6: Advanced Patterns

### 6.1 Context Window Sliding

For very long tasks, implement sliding window:

```markdown
## Sliding Window Strategy

When context exceeds 150K tokens:

1. **Archive**: Save detailed history to `.claude/archive/`
2. **Summarize**: Create summary of archived content
3. **Retain**: Keep last 50K of active conversation
4. **Reference**: Point to archive for details if needed

Example flow:
```
[Session at 180K tokens]
→ Archive messages 0-100K to archive_001.md
→ Create 5K summary of archived content
→ Continue with 85K context (5K summary + 80K recent)
→ If user asks about archived topic, read from archive
```
```

### 6.2 Multi-File Context Management

When working across many files:

```markdown
<!-- .claude/commands/load-feature.md -->
# Load Feature Context

Given a feature name, load all related files:

1. Find feature files: `grep -r "FEATURE_NAME" src/`
2. Load test files: `tests/**/test_*FEATURE_NAME*`
3. Load related configs: `config/*FEATURE_NAME*`
4. Summarize dependencies

Usage: /load-feature auth
```

### 6.3 Context Compression Techniques

```python
# Strategies for reducing context size

class ContextCompressor:
    """Compress context while preserving meaning."""

    @staticmethod
    def compress_code(code: str) -> str:
        """Remove comments and collapse whitespace in code."""
        lines = code.split('\n')
        compressed = []
        for line in lines:
            # Remove comment-only lines
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue
            # Remove inline comments
            if '#' in line:
                line = line.split('#')[0].rstrip()
            if '//' in line:
                line = line.split('//')[0].rstrip()
            if line.strip():
                compressed.append(line)
        return '\n'.join(compressed)

    @staticmethod
    def compress_json(json_str: str) -> str:
        """Minify JSON."""
        import json
        return json.dumps(json.loads(json_str), separators=(',', ':'))

    @staticmethod
    def summarize_test_output(output: str, max_lines: int = 20) -> str:
        """Summarize test output to key failures."""
        lines = output.split('\n')

        # Extract summary line
        summary = [l for l in lines if 'passed' in l or 'failed' in l]

        # Extract failures
        failures = []
        in_failure = False
        for line in lines:
            if 'FAILED' in line or 'ERROR' in line:
                in_failure = True
            if in_failure:
                failures.append(line)
                if len(failures) > max_lines:
                    failures.append('... (truncated)')
                    break

        return '\n'.join(summary + failures)
```

---

## Part 7: Decision Framework

### Context Loading Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│              CONTEXT LOADING DECISION TREE                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                 What type of task?                           │
│                        │                                     │
│        ┌───────────────┼───────────────┐                    │
│        │               │               │                     │
│        ▼               ▼               ▼                     │
│   Quick Fix      Feature Work    Architecture               │
│        │               │               │                     │
│        │               │               │                     │
│        ▼               ▼               ▼                     │
│   Load only       Load module      Load full                │
│   target file     + tests +        project                  │
│   (~5K tokens)    related          context                  │
│                   (~30K tokens)    (~80K tokens)            │
│                                                              │
│                                                              │
│   CONTEXT BUDGET GUIDE:                                      │
│   ─────────────────────                                      │
│   • Bug fix: 10-20K tokens (target file + error context)    │
│   • Feature: 30-50K tokens (module + interfaces + tests)    │
│   • Refactor: 50-80K tokens (affected area + dependencies)  │
│   • Architecture: 80-120K tokens (broad view + decisions)   │
│   • Always reserve 50K for conversation + responses         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Session Management Matrix

| Session State | Token Count | Action | Command |
|--------------|-------------|--------|---------|
| Fresh start | 0 | Load relevant context | `/load-feature X` |
| Mid-task | <100K | Continue | (none) |
| Getting full | 100-150K | Compress | `/compact` |
| Task complete | Any | Save and clear | Checkpoint → `/clear` |
| Context overflow | >180K | Emergency compress | `/compact --aggressive` |

---

## Checklist

### CLAUDE.md Setup
- [ ] Global CLAUDE.md in `~/.claude/`
- [ ] Project CLAUDE.md in repo root
- [ ] Module CLAUDE.md for complex areas
- [ ] Stable content before volatile content
- [ ] Minimum 1024 tokens for caching benefit

### Session Management
- [ ] Use `/clear` between unrelated tasks
- [ ] Use `/compact` for long-running tasks
- [ ] Create checkpoints for complex work
- [ ] Request session summaries before ending

### Context Optimization
- [ ] Targeted file reading (not whole files)
- [ ] Grep before read pattern
- [ ] Custom commands for common contexts
- [ ] Token budget awareness

### Memory Persistence
- [ ] Architecture decisions in `.claude/memory/`
- [ ] Session summaries saved
- [ ] Custom commands documented

---

## Troubleshooting

### Context Overflow Errors

**Symptom**: "Context length exceeded" errors

**Fixes**:
1. Run `/compact` immediately
2. Use targeted reads instead of full files
3. Clear irrelevant conversation history
4. Archive completed subtasks

### Poor Cache Hit Rate

**Symptom**: Costs not decreasing despite caching

**Causes**:
1. System prompt changing → Stabilize CLAUDE.md
2. Tool order changing → Fix tool definition order
3. Context prefix varying → Put stable content first
4. Sessions too short → Maintain longer sessions

### Slow Response Times

**Symptom**: Long waits for responses

**Causes**:
1. Too much context loaded → Reduce to essentials
2. No caching → Check cache configuration
3. Complex queries → Break into smaller steps

### Lost Context Between Sessions

**Symptom**: Claude doesn't remember previous work

**Fixes**:
1. Create explicit checkpoints
2. Use `.claude/memory/` for persistent decisions
3. Reference checkpoint in new session
4. Use `/resume` if available

---

## Resources

### Key Files
- `~/.claude/CLAUDE.md` - Global instructions
- `.claude/settings.json` - Project settings
- `.claude/memory/` - Persistent memory
- `.claude/commands/` - Custom commands

### Token Limits
- **Claude 3.5 Sonnet**: 200K context
- **Claude 3 Opus**: 200K context
- **Claude 3 Haiku**: 200K context
- **Prompt caching minimum**: 1024 tokens

### Cost Reference
- Input tokens: $3/million (uncached)
- Input tokens: $0.30/million (cached) - 90% savings
- Output tokens: $15/million
- Cache write: $3.75/million (one-time)
