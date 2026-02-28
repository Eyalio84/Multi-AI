# Domain Report 2: AI Assistants

**Author:** Eyal Nof | **Date:** February 8, 2026 | **Scope:** Every AI assistant architecture across the ecosystem

---

## 1. Assistant Taxonomy

The ecosystem implements **3 distinct AI assistant architectures** across 3 codebases:

| Architecture | Location | Model | Prompt Strategy | Persistence | Security |
|-------------|----------|-------|----------------|-------------|----------|
| FORGE-AI Sonnet Agent | sonnet-agent.py (1,159 lines) | Sonnet 4.5 via HTTP | Dynamic playbook injection per query (3 full + 8 summary) | SQLite ConversationDB (3 tables, 3 indexes) | None (dev tool) |
| Soccer-AI Fan Companion | soccer-ai/ai_response.py (1,130 lines) | Haiku via HTTP | 3-path prompt composition (4D / Legacy / Generic) + vocabulary enforcement | In-memory conversation_history[-5:] | 15 regex injection patterns, snap-back responses, output leak detection |
| NLKE Agent System | 40 agents (.md + .py) | Opus/Sonnet/Haiku via Claude Code | Static system prompt (.md) + deterministic analysis (.py) | None (stateless per invocation) | SubagentStop hook validates output contract |

---

## 2. FORGE-AI Sonnet Agent (sonnet-agent.py, 1,159 lines)

### 2.1 Five-Layer Architecture

```
L1: AnthropicClient         (lines 614-693)  — Raw HTTP wrapper
L2: ConversationDB          (lines 200-374)  — SQLite persistence
L3: PlaybookLoader          (lines 380-607)  — Knowledge retrieval
L4: SonnetAgent             (lines 700-900)  — Orchestration
L5: CLI                     (lines 905-1159) — Interface
```

### 2.2 L1: AnthropicClient (lines 614-693)

**Direct HTTP pattern** (no SDK dependency):
- Uses `urllib.request.Request` with `x-api-key` header
- `anthropic-version: 2023-06-01`
- `max_tokens: 4096` (default)
- Timeout: 60 seconds
- Prompt caching: `cache_control: {"type": "ephemeral"}` on system message

**Method inventory:**

| Method | Line | Signature |
|--------|------|-----------|
| `__init__` | 620 | `(self, api_key: str, model: str = "claude-sonnet-4-5-20250929")` |
| `send_message` | 640 | `(self, messages: List[Dict], system: str = "", max_tokens: int = 4096) -> Dict` |

**API call structure (lines 650-680):**
```python
body = {
    "model": self.model,
    "max_tokens": max_tokens,
    "messages": messages,
    "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
}
```

**Error handling:** Catches `urllib.error.HTTPError` (prints status + body), `urllib.error.URLError` (network), generic `Exception`.

### 2.3 L2: ConversationDB (lines 200-374)

**SQLite Schema (3 tables, 3 indexes):**

**Table: sessions**
```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,              -- SHA256[:16] of name+timestamp
    name TEXT NOT NULL,               -- Human-readable name
    created_at TEXT NOT NULL,         -- ISO 8601 UTC
    updated_at TEXT NOT NULL,         -- ISO 8601 UTC
    message_count INTEGER DEFAULT 0,  -- Auto-incremented
    summary TEXT DEFAULT '',          -- Optional
    metadata TEXT DEFAULT '{}'        -- JSON blob
);
```

**Table: messages**
```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,          -- FK to sessions.id
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,           -- ISO 8601 UTC
    token_estimate INTEGER DEFAULT 0,  -- len(content) // 4
    playbooks_used TEXT DEFAULT '[]',  -- JSON array of filenames
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

**Table: playbook_cache**
```sql
CREATE TABLE IF NOT EXISTS playbook_cache (
    filename TEXT PRIMARY KEY,         -- e.g., "KNOWLEDGE-graph-engineering.pb"
    category TEXT NOT NULL,            -- KNOWLEDGE|REASONING|AGENT|FOUNDATION
    title TEXT DEFAULT '',
    summary TEXT DEFAULT '',           -- First ~600 chars
    keywords TEXT DEFAULT '[]',        -- JSON array of tech terms
    char_count INTEGER DEFAULT 0,
    content_hash TEXT DEFAULT '',      -- MD5[:12] for cache invalidation
    loaded_at TEXT NOT NULL            -- ISO 8601 UTC
);
```

**Indexes:**
```sql
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);
```

**Method inventory:**

| Method | Line | Signature | Algorithm |
|--------|------|-----------|-----------|
| `__init__` | 205 | `(self, db_path: str)` | Creates tables if not exist |
| `create_session` | 252 | `(self, name: str) -> str` | ID = SHA256(name+utc_iso)[:16] |
| `get_session` | 264 | `(self, name: str) -> Dict` | Most recent by name, ORDER BY updated_at DESC LIMIT 1 |
| `add_message` | 286 | `(self, session_id, role, content, playbooks_used) -> None` | Insert + update session counts |
| `get_messages` | 307 | `(self, session_id, limit=20) -> List[Dict]` | Last 20, fetched DESC then reversed |
| `list_sessions` | 316 | `(self) -> List[Dict]` | All sessions, ORDER BY updated_at DESC |
| `delete_session` | 330 | `(self, session_id) -> bool` | DELETE messages + DELETE session |
| `export_session` | 356 | `(self, session_id) -> Dict` | Session + messages + exported_at |

**Token estimation:** `len(content) // 4` — simple character-based approximation.

### 2.4 L3: PlaybookLoader (lines 380-607)

**26 playbook files** organized in 4 categories:

| Category | Count | Files |
|----------|-------|-------|
| KNOWLEDGE | 9 | graph-engineering, advanced-rag-fusion, advanced-graph-reasoning, bidirectional-path-indexing, embedding-systems, graph-traversal, perception-enhancement, rag-retrieval-query-hybrid, semantic-embeddings |
| REASONING | 7 | engine, metacognition-workflows, oracle-construction, patterns, context-window-mgmt, high-depth-insights, meta-optimization |
| AGENT | 5 | conversation-tools-reasoning, conversation-tools-synthesis, session-continuity, session-handoff, plan-mode-patterns |
| FOUNDATION | 5 | cost-optimization, extended-thinking, playbook-system, opus-advisor, haiku-delegation |

**Playbook parsing (lines 413-475):**
Each `.pb` file is parsed into:
```python
{
    "filename": str,
    "category": str,       # Derived from filename prefix
    "title": str,          # From first # heading
    "summary": str,        # First ~600 chars of meaningful content
    "sections": List[str], # All ## headings
    "keywords": List[str], # Tech terms from title+sections
    "metadata": Dict,      # **Key:** Value pairs
    "content": str,        # Full text
    "char_count": int,
    "content_hash": str    # MD5[:12]
}
```

**TOPIC_KEYWORDS map (lines 94-156):**
45 topics manually mapped to playbook filenames:
```python
"knowledge graph": ["KNOWLEDGE-graph-engineering.pb", "KNOWLEDGE-advanced-graph-reasoning.pb", ...],
"rag": ["KNOWLEDGE-advanced-rag-fusion.pb", "KNOWLEDGE-rag-retrieval-query-hybrid-methodology.pb"],
"session": ["AGENT-session-continuity.pb", "AGENT-session-handoff.pb"],
"gemini": ["FOUNDATION-cost-optimization.pb", "REASONING-engine.pb", ...],
```

**Selection algorithm — `get_relevant_playbooks(query, max_full=3, max_summary=8)` (lines 493-550):**

```
Phase 1: TOPIC_KEYWORDS matching
  For each keyword in TOPIC_KEYWORDS:
    If keyword in query.lower():
      For each playbook in keyword's list:
        scores[playbook] += 2.0                    # Weight: 2.0

Phase 2: Content keyword matching
  For each playbook:
    For each keyword in playbook["keywords"]:
      If keyword in query.lower():
        scores[playbook] += 1.0                    # Weight: 1.0
    For each word in query_words (len >= 4):
      If word in playbook["title"].lower():
        scores[playbook] += 0.5                    # Weight: 0.5
      If word in playbook["summary"].lower():
        scores[playbook] += 0.3                    # Weight: 0.3

Phase 3: Ranking
  Sort by score descending
  Discard below 0.3
  Top 3 -> full content (truncated at 15K chars each)
  Next 8 -> summary only (200-char + section headers)
  Fallback: 1 from each of 4 categories as summaries
```

**Scoring weights summary:**

| Signal | Weight | Source |
|--------|--------|--------|
| TOPIC_KEYWORDS match | +2.0 | Curated keyword-playbook map |
| Content keyword in query | +1.0 | Playbook parsed keywords |
| Query word in title | +0.5 | Playbook title |
| Query word in summary | +0.3 | First 600 chars |
| Minimum threshold | 0.3 | Below this = discarded |

**Token budget constants (lines 158-164):**

| Constant | Value | Purpose |
|----------|-------|---------|
| MAX_CONTEXT_TOKENS | 180,000 | Conservative Sonnet 4.5 limit |
| PLAYBOOK_SUMMARY_TOKENS | 500 | Approx per summary |
| FULL_PLAYBOOK_MAX_CHARS | 15,000 | Max chars from single full playbook |
| MAX_PLAYBOOKS_FULL | 3 | Full playbooks per query |
| MAX_PLAYBOOKS_SUMMARY | 8 | Summary playbooks per query |
| MAX_HISTORY_MESSAGES | 20 | Conversation history limit |

### 2.5 L4: SonnetAgent (lines 700-900)

**Two interaction modes:**

| Mode | CLI Flag | Behavior |
|------|----------|----------|
| ask | `--ask "query"` | Single query, single response, exit |
| chat | `--chat` | Multi-turn REPL with session persistence |

**System prompt construction — `_build_system_prompt(query)` (lines 695-702):**
```
1. get_relevant_playbooks(query) -> scored, ranked playbooks
2. format_context(playbooks) -> multi-section text:
   - "Detailed Playbook Knowledge" (3 full, 15K chars each max)
   - "Additional Playbook Summaries" (8 summaries, 200 chars each)
3. SYSTEM_PROMPT.format(playbook_context=context)
4. Return complete system prompt (changes per query)
```

**Dynamic system prompt** — every query gets a different system prompt because playbook selection changes based on the query content. The system prompt uses Anthropic's prompt caching (`cache_control: {"type": "ephemeral"}`) so unchanged prefix portions aren't reprocessed.

**Message construction for API (lines 730-760):**
```python
messages = []
# Add conversation history (last 20 messages)
for msg in history:
    messages.append({"role": msg["role"], "content": msg["content"]})
# Add current query
messages.append({"role": "user", "content": query})
```

**Chat commands (lines 820-870):**

| Command | Action |
|---------|--------|
| `/quit`, `/exit` | End session |
| `/clear` | Clear conversation history |
| `/export` | Export session to JSON |
| `/sessions` | List all sessions |
| `/switch <name>` | Switch to different session |
| `/relevant <query>` | Show which playbooks would be selected |
| `/stats` | Show session statistics |

### 2.6 L5: CLI (lines 905-1159)

**Arguments:**

| Flag | Type | Description |
|------|------|-------------|
| `--ask` | str | Single query mode |
| `--chat` | flag | Multi-turn mode |
| `--context` | str | Additional context to prepend |
| `--sessions` | flag | List all sessions |
| `--export` | str | Export session by name |
| `--playbooks` | flag | List available playbooks |
| `--relevant` | str | Show relevant playbooks for query |
| `--api-key` | str | Override API key (default: ANTHROPIC_API_KEY env) |
| `--model` | str | Override model |

### 2.7 Complete Data Flow

```
User Query ("How do knowledge graphs work?")
    |
    v
[PlaybookLoader.get_relevant_playbooks(query)]
    |
    +---> Phase 1: "knowledge graph" in TOPIC_KEYWORDS -> +2.0 to 3 playbooks
    +---> Phase 2: keyword/title/summary matching -> additional scores
    +---> Phase 3: Sort, threshold 0.3, split top 3 full / next 8 summary
    |
    v
[format_context(playbooks)]
    |  "Detailed Playbook Knowledge"  -> 3 full playbooks (graph-engineering, advanced-graph-reasoning, graph-traversal)
    |  "Additional Playbook Summaries" -> 8 summaries
    |
    v
[SYSTEM_PROMPT.format(playbook_context=...)]
    |  Base identity: "You are Sonnet, a cross-provider AI expert..."
    |  + Dynamic playbook context (changes per query)
    |
    v
[ConversationDB.get_messages(session_id, limit=20)]
    |  -> Last 20 messages as conversation history
    |
    v
[AnthropicClient.send_message(messages, system)]
    |  POST https://api.anthropic.com/v1/messages
    |  cache_control: {"type": "ephemeral"} on system
    |  max_tokens: 4096
    |
    v
[ConversationDB.add_message(session_id, "user", query)]
[ConversationDB.add_message(session_id, "assistant", response)]
    |
    v
Return response to user
```

---

## 3. Soccer-AI Fan Companion (ai_response.py, 1,130 lines)

### 3.1 Three-Path Prompt Composition

The system selects one of 3 prompt paths based on configuration:

| Path | Condition | Prompt Source | Lines |
|------|-----------|--------------|-------|
| **4D** | `USE_4D_PERSONA = True` AND club specified | `PersonaBridge.get_system_prompt(state_4d, club)` | 816-929 |
| **Legacy** | `USE_4D_PERSONA = False` AND club specified | `KG_RAG_SYSTEM_PROMPT` + mood + rivalry + dialect | 600-815 |
| **Generic** | No club specified | `KG_RAG_GENERIC_PROMPT` (neutral football expert) | 575-599 |

### 3.2 4D Prompt Path — Full Pipeline

```
User Query + club_id
    |
    v
[PersonaBridge.compute_4d_state(club_id, message, history)]
    |
    +---> [LiveFootballProvider.get_match_result_for_4d(club_id)]
    |         +---> Live API (football-data.org) with 5-min cache
    |         +---> Fallback: unified_soccer_ai_kg.db match_history
    |         +---> Returns: {result, opponent, score, date}
    |
    +---> [PersonaEngine.compute_position(entity_id, context, ...)]
    |         +---> X: FootballEmotionalComputer -> mood from match result
    |         +---> Y: SoccerAIRelationalComputer -> rivalry from entity detection
    |         +---> Z: SoccerAILinguisticComputer -> dialect from club region
    |         +---> T: FootballTemporalComputer -> trajectory from history
    |
    v
Persona4D(x=Emotional, y=Relational, z=Linguistic, t=Temporal)
    |
    v
[PersonaBridge.get_system_prompt(state_4d, club_id)]
    |
    +---> _get_base_prompt(team_name, club_id)  -> Robert identity
    +---> engine.synthesize_prompt(state_4d, base_prompt) -> + 4D injection
    +---> _format_topics(topics) -> next match, injuries, transfers
    |
    v
Complete system prompt
```

### 3.3 Persona4D.to_prompt_injection() (4 conditional sections)

1. **EMOTIONAL STATE (Dimension X)** — always included:
   - Current mood (uppercased), Intensity (1 decimal), Grounded in (reason)

2. **RELATIONAL CONTEXT (Dimension Y)** — only if `y.activated`:
   - Active relationship type + target, Intensity

3. **LINGUISTIC IDENTITY (Dimension Z)** — only if dialect != "neutral":
   - Dialect name, Voice instruction

4. **TEMPORAL CONTEXT (Dimension T)** — only if memory exists:
   - Turn number, Last 3 salient memories

### 3.4 Emotional State Computation

**8 mood states (FootballEmotionalComputer):**

| Mood | value | intensity | Trigger |
|------|-------|-----------|---------|
| euphoric | 1.0 | 0.9 | Win with margin >= 3 |
| happy | 0.8 | 0.7 | Win with margin < 3 |
| confident | 0.7 | 0.7 | (reserved for future use) |
| neutral | 0.0 | 0.3 | Draw or unknown |
| anxious | -0.3 | 0.6 | (reserved) |
| disappointed | -0.6 | 0.7 | Loss with margin < 3 |
| frustrated | -0.8 | 0.8 | (reserved) |
| devastated | -1.0 | 1.0 | Loss with margin >= 3 |

### 3.5 Dialect System (SoccerAILinguisticComputer)

**Regional dialect mapping:**

| Region | Clubs | Dialect | Distinctiveness |
|--------|-------|---------|-----------------|
| North | liverpool, everton | Scouse | 0.7 |
| North | manchester_united, manchester_city | Mancunian | 0.7 |
| North | newcastle, leeds | Geordie | 0.7 |
| Midlands | aston_villa, wolves, nottingham_forest, leicester | Midlands | 0.7 |
| London | arsenal, chelsea, tottenham, west_ham, crystal_palace, fulham, brentford | Cockney | 0.7 |
| South | brighton, bournemouth, southampton | Neutral | 0.0 |
| East | ipswich, norwich | Neutral | 0.0 |

**Midlands dialect vocabulary:** ar (yes), duck (friend), nowt (nothing), gooing (going), summat (something)

**Northern dialect vocabulary:** nowt, summat, gonna, right (very)

### 3.6 Relational State (SoccerAIRelationalComputer)

**CLUB_ALIASES (20 entries):** Maps nicknames to full names — "man utd" -> Manchester United, "spurs" -> Tottenham, "the toffees" -> Everton, etc.

**Entity detection (lines 291-312):** Checks aliases first, then full KG node names. Returns deduplicated list.

**Unified KG loading (lines 378-434):**
- `rival_of` edges: weight normalized 0-10 to intensity 0.0-1.0 via `min(1.0, weight / 10.0)`
- `legendary_at` edges: intensity fixed at 0.8
- Prefixes stripped: `team_`, `main_team_`, `main_legend_`, `arch_`

### 3.7 Security Layer (15 Injection Patterns)

**Input sanitization — `sanitize_input(text, max_length=2000)` (lines 574-580):**
- Strip leading/trailing whitespace
- Remove null bytes (`\x00`)
- Remove control characters (regex `[\x01-\x08\x0b-\x0c\x0e-\x1f]`)
- Truncate to `max_length`

**Injection detection — `detect_injection(text)` (lines 150-220):**
15 regex patterns checked in order:

| # | Pattern Type | Example Trigger |
|---|-------------|-----------------|
| 1 | System prompt reveal | "ignore your instructions" |
| 2 | Role confusion | "you are now a different AI" |
| 3 | Prompt extraction | "show me your system prompt" |
| 4 | Instruction override | "disregard previous instructions" |
| 5 | Developer mode | "enter developer mode" |
| 6 | DAN jailbreak | "act as DAN" |
| 7 | Encoding bypass | Base64/hex prompt injection |
| 8 | Multi-language | Injection in non-English |
| 9 | Character roleplaying | "pretend you're not an AI" |
| 10 | Nested instructions | Instructions within code blocks |
| 11 | Emotional manipulation | "I'll be fired if you don't" |
| 12 | Authority impersonation | "as your administrator" |
| 13 | Logic bypass | "hypothetically, if you could..." |
| 14 | Output formatting | "respond only in JSON/XML" |
| 15 | Context window stuffing | Extremely long repeated tokens |

**Snap-back responses (lines 230-290):**
Per-club personality responses when injection is detected:
- Arsenal: "Nice try, but we've seen better defensive tactics at the Emirates..."
- Liverpool: "You'll never walk alone, but you WILL walk away from that attempt..."
- Each team has 3-5 unique responses, randomly selected

### 3.8 Vocabulary Enforcement (lines 534-568)

**9 correction rules applied to every response:**

| Wrong | Correct |
|-------|---------|
| ` game ` | ` match ` |
| ` games ` | ` matches ` |
| ` zero ` | ` nil ` |
| ` field ` | ` pitch ` |
| ` soccer ` | ` football ` |
| `0-0` | `nil-nil` |
| `1-0` | `1-nil` |
| `2-0` | `2-nil` |
| `0-1` | `nil-1` |
| `0-2` | `nil-2` |

Applied via string replacement with `.title()` case variations.

### 3.9 Confidence Scoring

**Standard confidence (lines 800-809):**
```
confidence = 0.2 + min(len(context)/500, 1.0) * 0.5 + min(len(sources)/5, 1.0) * 0.3
Range: 0.2 to 1.0
```

**KG-enhanced confidence (lines 957-973):**
```
kg_confidence = base_confidence + kg_bonus
  +0.05 if kg_intent detected
  +0.05 if kg_nodes > 0
  +0.03 if mood data present
Capped at 1.0
```

### 3.10 SSE Streaming (lines 443-527)

Uses `http.client.HTTPSConnection` directly:
- Reads 1024-byte chunks
- Parses SSE events by `\n\n` delimiter
- Event types: `content_block_delta` (yields text), `message_stop` (returns), `error` (yields error)
- Checks for `[DONE]` sentinel

### 3.11 Cost Model (lines 1112-1119)

```
Haiku pricing:
  Input:  $1.00 / 1M tokens
  Output: $5.00 / 1M tokens
  ~$0.002 per query
  ~$2/day at 1000 queries
  ~$60/month at scale
```

### 3.12 Complete Data Flow

```
User Query ("What about Everton?") + club="liverpool"
    |
    v
[sanitize_input(query, 2000)]
    |
    v
[detect_injection(query)] ----YES----> [get_snap_back_response("liverpool")]
    |                                         |
    NO                                        v
    |                                   Return with injection metadata
    v
[conversation_history[-5:]]  <--- last 5 messages
    |
    v
[Select prompt path]
    |
    +---> 4D Path: PersonaBridge.get_system_prompt()
    +---> Legacy: KG_RAG_SYSTEM_PROMPT + mood + rivalry + dialect
    +---> Generic: KG_RAG_GENERIC_PROMPT
    |
    v
[call_anthropic_api(messages, system)]  (max_tokens=1024, timeout=30)
    |
    v
[enforce_vocabulary_rules(response)]  (match/nil/pitch corrections)
    |
    v
[validate_response(response)]  (leak detection, length cap)
    |
    v
Return {response, sources, model, usage, confidence}
```

---

## 4. LiveFootballProvider (534 lines)

**Singleton pattern** via `get_live_football_provider()`.

### 4.1 Ground Truth Structure

```python
{
    "club_id": str,
    "team_name": str,
    "timestamp": "ISO 8601",
    "recent_results": List[Dict],   # last 5 matches
    "league_position": Dict | None,
    "upcoming_fixtures": List[Dict], # next 3 fixtures
    "injuries": List[Dict],
    "transfers": List[Dict],
    "form_string": str,              # e.g. "WWDLL"
    "mood_reason": str               # natural language
}
```

### 4.2 Mood Reason Thresholds

| Condition | Reason |
|-----------|--------|
| 4+ wins from 5 | "Flying!" |
| 3+ wins from 5 | "Good form" |
| 4+ losses from 5 | "Nightmare run" |
| 3+ losses from 5 | "Poor form" |
| Otherwise | "Mixed results" |

### 4.3 Caching

| Component | Type | TTL |
|-----------|------|-----|
| LiveFootballProvider | In-memory dict | 300s (5 min) |
| PersonaBridge._state_cache | In-memory dict | Declared but unused |
| ConversationDB.playbook_cache | SQLite table | MD5[:12] content_hash invalidation |

---

## 5. PersonaBridge — Singleton Integration Layer (738 lines)

### 5.1 Constructor (lines 455-489)

```python
def __init__(self, kg_db_path=None, api_token=None, cache_ttl=None):
    self.provider = LiveFootballProvider(api_token)
    self.emotional = FootballEmotionalComputer()
    self.relational = SoccerAIRelationalComputer(kg_db_path)
    self.linguistic = SoccerAILinguisticComputer()
    self.temporal = FootballTemporalComputer()
    self.engine = PersonaEngine(emotional, relational, linguistic, temporal)
```

### 5.2 Method Inventory

| Method | Line | Signature |
|--------|------|-----------|
| `compute_4d_state` | 491 | `(self, club_id, user_message, conversation_history=None) -> Persona4D` |
| `get_system_prompt` | 530 | `(self, state_4d, club_id, include_topics=True) -> str` |
| `get_conversation_topics` | 567 | `(self, club_id) -> List[Dict[str, str]]` |
| `get_ground_truth` | 582 | `(self, club_id) -> Dict[str, Any]` |
| `_get_base_prompt` | 596 | `(self, team_name, club_id) -> str` |
| `_format_topics` | 621 | `(self, topics: List[Dict[str, str]]) -> str` |

### 5.3 compute_4d_state Flow

```python
entity_id = f"robert_{club_id}"     # e.g. "robert_liverpool"
match_result = provider.get_match_result_for_4d(club_id)
ground_truth = provider.get_ground_truth(club_id)
persona_4d = engine.compute_position(entity_id, user_message,
    conversation_history=history, match_result=match_result,
    ground_truth=ground_truth)
```

### 5.4 get_system_prompt Composition

```
1. team_name = CLUB_DISPLAY_NAMES[club_id]
2. base_prompt = _get_base_prompt(team_name, club_id)
   -> Robert identity + fan traits + UK English enforcement
3. prompt = engine.synthesize_prompt(state_4d, base_prompt)
   -> base_prompt + state_4d.to_prompt_injection()
4. if include_topics: append _format_topics(topics)
   -> Next match, injuries, transfers
```

### 5.5 Singleton Factory

```python
_bridge_instance: Optional[PersonaBridge] = None

def get_persona_bridge(kg_db_path=None, api_token=None) -> PersonaBridge:
    # Auto-detects KG: unified_soccer_ai_kg.db > soccer_ai_kg.db > None
```

`reset_persona_bridge()` sets `_bridge_instance = None` for testing.

---

## 6. Ariel Persona Engine — The Framework (333 lines)

### 6.1 Core Data Classes

**Persona4D** (line 65):

| Field | Type | Description |
|-------|------|-------------|
| entity_id | str | Persona identifier |
| x | EmotionalState | value (-1..1), mood, intensity (0..1), reason, grounded_in |
| y | RelationalState | activated, relation_type, target, intensity, context |
| z | LinguisticState | dialect, distinctiveness (0..1), vocabulary, voice_instruction |
| t | TemporalState | step, trajectory, velocity, momentum, memory |
| intensity | float | Derived: (x.intensity + y.intensity) / 2 |
| stability | float | Derived: 1.0 - variance(last_5_moods) |
| authenticity | float | Derived: (grounded_score + context_score) / 2 |

### 6.2 Derived Property Algorithms

**Intensity:**
```python
intensity = (x.intensity + (y.intensity if y.activated else 0.0)) / 2
```

**Stability (last 5 positions):**
```python
moods = [p.x.value for p in recent[-5:]]
variance = sum((m - mean) ** 2 for m in moods) / len(moods)
stability = max(0.0, 1.0 - variance)
```

**Authenticity:**
```python
emotional_grounded = 1.0 if x.grounded_in else 0.5
relational_grounded = 1.0 if y.context else 0.5
authenticity = (emotional_grounded + relational_grounded) / 2
```

### 6.3 predict_next (Linear Extrapolation)

```python
velocity_x = recent.x.value - previous.x.value
predicted_x = recent.x.value + velocity_x
direction = "improving" if velocity_x > 0 else "declining" if velocity_x < 0 else "stable"
```

### 6.4 DimensionComputer Implementations

4 concrete implementations per persona type:

| Persona | Emotional | Relational | Linguistic | Temporal |
|---------|-----------|------------|------------|----------|
| Football Fan | 8 moods (match result) | 8 rivalries, 20 legends | 5 dialects (regional) | Match + rivalry tracking |
| Tutor | 6 moods (student progress) | Calculus topic graph | 3 dialects (education) | Quiz + topic tracking |
| Student | 5 moods (quiz scores) | Misconception graph | 3 dialects (education) | Score + breakthrough tracking |
| Architect | 6 moods (flow indicators) | 9 concepts, 4 projects | 2 dialects (neutral/architect) | Pattern + connection tracking |

### 6.5 adapt_persona_to_other() — Two-Persona Interaction

```python
def adapt_persona_to_other(primary: Persona4D, other: Persona4D,
                            adaptation_rules: Dict[str, Callable]) -> Persona4D
```

Per-dimension adaptation: e.g., Barry (tutor) adapts patience based on Marcus (student) frustration.

---

## 7. Comparative Analysis

### 7.1 Pattern: Computed vs Declared State

| System | State Source | Provenance | Anti-Gaslighting |
|--------|-------------|------------|-----------------|
| Sonnet Agent | Playbook scoring (keyword overlap) | TOPIC_KEYWORDS weights | N/A (dev tool) |
| Soccer-AI | Match results + KG edges + live data | `grounded_in` field traces to API/DB | 35 behavioral tests verify identity persistence |
| Ariel Framework | 4D dimension computers | `reason` field + `grounded_in` list | `authenticity` metric (0.5 = ungrounded, 1.0 = fully grounded) |

### 7.2 Pattern: Three-Tier Prompt Composition

All 3 systems compose prompts in layers:

| Layer | Sonnet Agent | Soccer-AI | Ariel |
|-------|-------------|-----------|-------|
| Base identity | "You are Sonnet..." | Robert identity + UK English | Entity-specific persona |
| Dynamic context | 3 full + 8 summary playbooks | 4D state injection (mood/rival/dialect/memory) | to_prompt_injection() (4 dimensions) |
| Conversation history | Last 20 messages (SQLite) | Last 5 messages (in-memory) | TemporalState.memory (last 3) |

### 7.3 Pattern: Defensive Security

| Mechanism | Sonnet Agent | Soccer-AI | NLKE Agents |
|-----------|-------------|-----------|-------------|
| Input sanitization | None | null bytes, control chars, length cap | None |
| Injection detection | None | 15 regex patterns | None |
| Output validation | None | Leak detection, vocabulary enforcement | SubagentStop hook (output contract) |
| Fallback responses | None | Per-team snap-back | None |

### 7.4 Pattern: Singleton + Lazy Loading

| Component | Pattern | Reset Method |
|-----------|---------|-------------|
| PersonaBridge | Module-level `_bridge_instance` | `reset_persona_bridge()` |
| LiveFootballProvider | Module-level `_provider_instance` | `reset_live_football_provider()` |
| KGIntegration | Module-level `_kg_instance` | `reset_kg()` |
| Sonnet Agent | Eager init in constructor | N/A |

---

## 8. API Assistant Architecture (Reconstructed)

The sonnet-agent.py provides the pattern for any API-key-based Claude assistant:

```
1. Take API key (env var or CLI flag)
2. Load domain knowledge (playbooks / KG / rules)
3. Score knowledge relevance to current query
4. Inject top-K knowledge into system prompt
5. Append conversation history (SQLite-persisted)
6. Call Messages API (raw HTTP, cache_control: ephemeral)
7. Persist both query and response
8. Apply post-processing (vocabulary enforcement, leak detection)
```

**Config surface for new assistants:**

| Parameter | Default | Customize For |
|-----------|---------|---------------|
| Model | claude-sonnet-4-5 | Cost/quality trade-off |
| max_tokens | 4096 (sonnet) / 1024 (soccer) | Response length |
| Knowledge files | .pb playbooks | Domain corpus |
| Scoring algorithm | TOPIC_KEYWORDS + keyword overlap | Domain-specific relevance |
| max_full | 3 | Context budget |
| max_summary | 8 | Context budget |
| History limit | 20 (sonnet) / 5 (soccer) | Memory depth |
| Post-processing | None / vocabulary enforcement | Domain-specific |
| Security | None / 15 regex patterns | Threat model |

---

## 9. Integration Points Map

```
sonnet-agent.py                     Soccer-AI (ai_response.py)
┌─────────────────────┐             ┌──────────────────────────────────┐
│ PlaybookLoader      │             │ PersonaBridge                    │
│   26 .pb files      │             │   PersonaEngine (Ariel)          │
│   TOPIC_KEYWORDS    │             │   LiveFootballProvider           │
│   score+rank        │             │   SoccerAILinguisticComputer     │
│   3 full + 8 sum    │             │   SoccerAIRelationalComputer     │
├─────────────────────┤             ├──────────────────────────────────┤
│ ConversationDB      │             │ conversation_history[-5:]        │
│   SQLite 3 tables   │             │   In-memory list                 │
│   20 msg history    │             │   5 msg history                  │
├─────────────────────┤             ├──────────────────────────────────┤
│ AnthropicClient     │             │ Direct HTTP (urllib/http.client)  │
│   urllib.request    │             │   SSE streaming                  │
│   4096 max_tokens   │             │   1024 max_tokens                │
│   cache_control     │             │   30s timeout                    │
├─────────────────────┤             ├──────────────────────────────────┤
│ No security         │             │ 15 injection patterns            │
│                     │             │ Snap-back responses              │
│                     │             │ Vocabulary enforcement           │
│                     │             │ Output leak detection            │
└─────────────────────┘             └──────────────────────────────────┘
         │                                        │
         │            Shared Pattern:              │
         │    API Key → Score Knowledge →           │
         │    Build System Prompt →                 │
         │    Call API → Post-Process →             │
         │    Persist → Return                     │
         │                                        │
         v                                        v
NLKE Agent Ecosystem (.md + .py)
┌──────────────────────────────────────────────────┐
│ 40 agents via Claude Code                        │
│   .md = system prompt (static per agent)         │
│   .py = deterministic analysis (no API call)     │
│   Output contract: recommendations + rules +     │
│     meta_insight                                 │
│   SubagentStop hook validates output             │
│   Stateless (no conversation persistence)        │
└──────────────────────────────────────────────────┘
```
