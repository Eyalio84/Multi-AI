# FORGE-AI Sonnet Agent - Complete User Guide

**Version:** 1.0.0
**Created:** February 6, 2026
**Phase:** 8.5 - FORGE-AI Cross-Provider Reproducibility
**NLKE Version:** 7.5

---

## Table of Contents

1. [What Is the Sonnet Agent?](#what-is-the-sonnet-agent)
2. [Quick Start (5 Minutes)](#quick-start)
3. [Installation & Setup](#installation--setup)
4. [CLI Reference](#cli-reference)
5. [Modes of Operation](#modes-of-operation)
6. [Session Management](#session-management)
7. [Playbook System](#playbook-system)
8. [Chat Commands](#chat-commands)
9. [Context Management (How It Works)](#context-management)
10. [Cross-Provider Translation](#cross-provider-translation)
11. [Configuration](#configuration)
12. [Examples & Use Cases](#examples--use-cases)
13. [Architecture](#architecture)
14. [Troubleshooting](#troubleshooting)
15. [API Cost Reference](#api-cost-reference)

---

## 1. What Is the Sonnet Agent?

The FORGE-AI Sonnet Agent is a **persistent, expert AI assistant** powered by Claude Sonnet 4.5 with a pre-loaded knowledge base of 26 playbooks covering knowledge engineering, reasoning systems, agent patterns, and cost optimization.

**Key capabilities:**
- **Persistent memory** - Conversations are saved in SQLite. Come back tomorrow and pick up where you left off
- **26-playbook knowledge base** - 743 KB of expert knowledge across 4 domains, automatically loaded per query
- **Smart context management** - Only loads playbooks relevant to your question (saves tokens and money)
- **Cross-provider translation** - Bridges Claude and Gemini concepts, APIs, and capabilities
- **Zero SDK dependency** - Uses direct HTTP calls via `requests` (no `anthropic` package needed)
- **Named sessions** - Run multiple concurrent projects, each with its own conversation history

**Who is it for?**
- Gemini CLI users who need Claude expertise for knowledge engineering
- Developers building KGs, RAG systems, or agent architectures
- Anyone reproducing the FORGE-AI methodology across providers

---

## 2. Quick Start

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# 2. Ask a question
python3 sonnet-agent.py --ask "How do I build a knowledge graph with SQLite?"

# 3. Start an interactive chat session
python3 sonnet-agent.py --chat

# 4. Resume a named session later
python3 sonnet-agent.py --chat --context "my-project"
```

That's it. The agent loads 26 playbooks, picks the relevant ones for your query, calls Sonnet 4.5, and returns an expert answer.

---

## 3. Installation & Setup

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Any OS (Linux, macOS, Windows, Termux) |
| `requests` | Any | `pip install requests` |
| `sqlite3` | Built-in | Comes with Python |
| Anthropic API key | - | Get from https://console.anthropic.com |

### Step-by-Step Setup

```bash
# 1. Ensure Python 3.10+ is installed
python3 --version

# 2. Install requests (if not already installed)
pip install requests

# 3. Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

# To make it permanent, add to your shell profile:
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key"' >> ~/.bashrc
source ~/.bashrc

# 4. Verify playbooks are accessible (optional - agent will warn if missing)
python3 sonnet-agent.py --playbooks

# 5. Test with a question
python3 sonnet-agent.py --ask "What is FORGE-AI?"
```

### Playbook Directory

The agent expects playbooks at:
```
/storage/emulated/0/Download/gemini-3-pro/playbooks/playbooks-v2/
```

To use a custom location:
```bash
# Via command line
python3 sonnet-agent.py --chat --pb-dir /your/path/to/playbooks/

# Via environment variable
export FORGE_AI_PB_DIR="/your/path/to/playbooks/"
python3 sonnet-agent.py --chat
```

### Database Location

Conversation history is stored at `~/.forge-ai/sonnet-agent.db` by default.

To customize:
```bash
# Via command line
python3 sonnet-agent.py --chat --db-path /path/to/my.db

# Via environment variable
export FORGE_AI_DB="/path/to/my.db"
```

---

## 4. CLI Reference

### Complete Flag Reference

| Flag | Type | Description | Required |
|------|------|-------------|----------|
| `--ask QUESTION` | string | Ask a single question | One of --ask or --chat |
| `--chat` | flag | Start interactive chat mode | One of --ask or --chat |
| `--context NAME` | string | Named session for persistence | No (default: ephemeral or "default") |
| `--sessions` | flag | List all saved sessions | No |
| `--export NAME` | string | Export a session to JSON | No |
| `--delete-session NAME` | string | Delete a session | No |
| `--playbooks` | flag | List loaded playbooks with stats | No |
| `--relevant TOPIC` | string | Show relevant playbooks for a topic | No |
| `--api-key KEY` | string | API key (overrides env var) | No |
| `--model MODEL` | string | Model ID (default: claude-sonnet-4-5-20250929) | No |
| `--db-path PATH` | string | SQLite database path | No |
| `--pb-dir PATH` | string | Playbooks directory path | No |
| `--output FILE` / `-o` | string | Output file for --export or --ask | No |
| `--version` | flag | Show version number | No |
| `--help` / `-h` | flag | Show help message | No |

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required for --ask/--chat |
| `FORGE_AI_DB` | SQLite database path | `~/.forge-ai/sonnet-agent.db` |
| `FORGE_AI_PB_DIR` | Playbooks directory | (built-in path) |

---

## 5. Modes of Operation

### Mode 1: Single Question (`--ask`)

Ask one question, get one answer. Optionally save to a session.

```bash
# Ephemeral (not saved)
python3 sonnet-agent.py --ask "What's the difference between RAG and KG?"

# Saved to a named session
python3 sonnet-agent.py --ask "How do I extract entities?" --context "kg-tutorial"

# Follow up in the same session
python3 sonnet-agent.py --ask "What about relationships?" --context "kg-tutorial"

# Save response to file
python3 sonnet-agent.py --ask "Explain prompt caching" -o caching-guide.txt
```

**When to use:** Quick one-off questions, scripted workflows, piping to other tools.

### Mode 2: Interactive Chat (`--chat`)

Full interactive session with persistence and slash commands.

```bash
# New session (default name: "default")
python3 sonnet-agent.py --chat

# Named session
python3 sonnet-agent.py --chat --context "my-kg-project"

# Resume later (same command)
python3 sonnet-agent.py --chat --context "my-kg-project"
```

**When to use:** Extended work sessions, iterative development, exploratory research.

### Mode 3: Information Commands (No API key needed)

These commands work without an API key - they only access local data.

```bash
# List all loaded playbooks
python3 sonnet-agent.py --playbooks

# Check which playbooks match a topic
python3 sonnet-agent.py --relevant "graph traversal algorithms"

# List saved sessions
python3 sonnet-agent.py --sessions

# Export a session to JSON
python3 sonnet-agent.py --export "my-session" -o session-backup.json

# Delete a session
python3 sonnet-agent.py --delete-session "old-project"

# Show version
python3 sonnet-agent.py --version
```

---

## 6. Session Management

Sessions are the persistence layer. Each session has:
- A **name** (human-readable, like "my-kg-project")
- A unique **ID** (auto-generated hash)
- Complete **message history** (all user/assistant messages)
- **Timestamps** for creation and last update
- **Message count** tracking

### Creating Sessions

Sessions are created automatically when you use `--context`:

```bash
# Creates "my-project" session if it doesn't exist
python3 sonnet-agent.py --ask "How to build a KG?" --context "my-project"
```

In chat mode, `--context` resumes an existing session or creates a new one:
```bash
python3 sonnet-agent.py --chat --context "my-project"
# Output: "Resuming session 'my-project' (5 messages)" or "New session 'my-project' created"
```

### Listing Sessions

```bash
python3 sonnet-agent.py --sessions
```

Output:
```
Name                      ID           Messages Last Updated
----------------------------------------------------------------------
my-kg-project             a3f2b81c0e       42 2026-02-06T18:30:00
gemini-comparison         8b1e4a7d92       15 2026-02-06T16:45:00
default                   c7d9e2f1a3        8 2026-02-06T14:20:00
```

### Exporting Sessions

```bash
# Print to stdout
python3 sonnet-agent.py --export "my-project"

# Save to file
python3 sonnet-agent.py --export "my-project" -o my-project-export.json
```

Export format:
```json
{
  "session": {
    "id": "a3f2b81c0e",
    "name": "my-kg-project",
    "created_at": "2026-02-06T14:00:00+00:00",
    "updated_at": "2026-02-06T18:30:00+00:00",
    "message_count": 42
  },
  "messages": [
    {
      "role": "user",
      "content": "How do I build a knowledge graph?",
      "timestamp": "2026-02-06T14:00:01+00:00",
      "playbooks_used": ["KNOWLEDGE-graph-engineering.pb"]
    },
    ...
  ],
  "exported_at": "2026-02-06T19:00:00+00:00"
}
```

### Deleting Sessions

```bash
python3 sonnet-agent.py --delete-session "old-project"
# Output: Deleted session 'old-project' (15 messages)
```

### Switching Sessions in Chat Mode

Inside an active chat session, use `/switch`:
```
You> /switch new-project
Created new session 'new-project'

You> /switch my-kg-project
Switched to session 'my-kg-project' (42 messages)
```

---

## 7. Playbook System

The agent's knowledge base consists of 26 playbooks across 4 categories totaling 743 KB of expert content.

### Categories

| Category | Count | Content |
|----------|-------|---------|
| **KNOWLEDGE** | 9 | Knowledge graphs, RAG, embeddings, entity extraction, semantic search |
| **REASONING** | 7 | Reasoning engines, metacognition, oracle construction, patterns, context management |
| **AGENT** | 5 | Conversation patterns, session continuity, handoff protocols, plan mode |
| **FOUNDATION** | 5 | Cost optimization, extended thinking, playbook system, model selection |

### All 26 Playbooks

**KNOWLEDGE (9):**

| Playbook | Size | Focus |
|----------|------|-------|
| `KNOWLEDGE-graph-engineering.pb` | 44.2 KB | KG construction, entity extraction, SQLite schema, validation |
| `KNOWLEDGE-advanced-rag-fusion.pb` | 46.9 KB | Advanced RAG with graph fusion techniques |
| `KNOWLEDGE-advanced-graph-reasoning.pb` | 19.0 KB | Graph-based reasoning patterns |
| `KNOWLEDGE-bidirectional-path-indexing.pb` | 30.2 KB | Bidirectional path algorithms for KGs |
| `KNOWLEDGE-embedding-systems.pb` | 21.0 KB | Embedding architectures, semantic search |
| `KNOWLEDGE-graph-traversal.pb` | 12.7 KB | Graph traversal algorithms and strategies |
| `KNOWLEDGE-perception-enhancement.pb` | 8.4 KB | Entity perception and enhancement |
| `KNOWLEDGE-rag-retrieval-query-hybrid.pb` | 5.6 KB | Hybrid RAG-query methodology |
| `KNOWLEDGE-semantic-embeddings.pb` | 40.7 KB | Semantic embeddings at zero cost |

**REASONING (7):**

| Playbook | Size | Focus |
|----------|------|-------|
| `REASONING-engine.pb` | 27.8 KB | Reasoning engine design and operation |
| `REASONING-metacognition-workflows.pb` | 38.5 KB | Metacognition patterns and workflows |
| `REASONING-oracle-construction.pb` | 26.5 KB | Oracle system construction |
| `REASONING-patterns.pb` | 52.6 KB | Comprehensive reasoning patterns library |
| `REASONING-context-window-mgmt.pb` | 24.7 KB | Context window management strategies |
| `REASONING-high-depth-insights.pb` | 12.8 KB | Deep insight generation |
| `REASONING-meta-optimization.pb` | 21.6 KB | Meta-optimization patterns |

**AGENT (5):**

| Playbook | Size | Focus |
|----------|------|-------|
| `AGENT-conversation-tools-reasoning.pb` | 21.5 KB | Fractal reasoning composition |
| `AGENT-conversation-tools-synthesis.pb` | 12.3 KB | Synthesis patterns for conversations |
| `AGENT-session-continuity.pb` | 21.6 KB | 90% context preservation at 10% token cost |
| `AGENT-session-handoff.pb` | 30.6 KB | Session handoff protocols |
| `AGENT-plan-mode-patterns.pb` | 86.8 KB | Plan mode strategies and patterns |

**FOUNDATION (5):**

| Playbook | Size | Focus |
|----------|------|-------|
| `FOUNDATION-cost-optimization.pb` | 27.2 KB | 90-95% cost reduction guide |
| `FOUNDATION-extended-thinking.pb` | 28.6 KB | Extended thinking implementation |
| `FOUNDATION-playbook-system.pb` | 14.9 KB | The playbook system itself |
| `FOUNDATION-opus-advisor.pb` | 8.7 KB | Opus model advisor pattern |
| `FOUNDATION-haiku-delegation.pb` | 57.3 KB | Haiku delegation patterns |

### How Playbook Loading Works

When you ask a question, the agent:

1. **Scans your query** for topic keywords (e.g., "knowledge graph", "RAG", "cost")
2. **Scores each playbook** by relevance (keyword match + title match + summary match)
3. **Loads top 3** playbooks in **full detail** (complete content, up to 15KB each)
4. **Loads next 8** as **summaries** (title + section list, ~200 chars each)
5. **Injects into system prompt** so Sonnet has the knowledge to answer

This means the agent is never overwhelmed with all 743 KB - it smartly loads only what's needed.

### Checking Relevance

See which playbooks would load for a topic:

```bash
python3 sonnet-agent.py --relevant "knowledge graph construction"
```

Output:
```
Topic: 'knowledge graph construction'

Full context (3) - loaded in detail:
  [KNOWLEDGE] KNOWLEDGE-graph-engineering.pb (44.2 KB)
    Playbook 4: Knowledge Engineering with Claude
  [KNOWLEDGE] KNOWLEDGE-graph-traversal.pb (12.7 KB)
  [KNOWLEDGE] KNOWLEDGE-advanced-graph-reasoning.pb (19.0 KB)

Summary context (8) - referenced:
  [KNOWLEDGE] KNOWLEDGE-perception-enhancement.pb
  [KNOWLEDGE] KNOWLEDGE-advanced-rag-fusion.pb
  ...
```

---

## 8. Chat Commands

Inside interactive chat mode (`--chat`), these slash commands are available:

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/playbooks` | List all loaded playbooks with sizes |
| `/relevant <topic>` | Show which playbooks match a topic |
| `/history` | Show last 10 messages in current session |
| `/sessions` | List all saved sessions |
| `/switch <name>` | Switch to a different session (creates if new) |
| `/export [file]` | Export current session to JSON (to stdout or file) |
| `/stats` | Show current session statistics |
| `/clear` | Clear current session and start fresh |
| `/model` | Show current model being used |
| `quit` / `exit` | Save session and exit |

### Chat Command Examples

```
You> /stats
  Session: my-kg-project (id: a3f2b81c...)
  Messages: 42
  Token estimate: ~85,000
  Created: 2026-02-06T14:00:00
  Updated: 2026-02-06T18:30:00
  Playbooks loaded: 26

You> /relevant embedding vector search
Full context (3):
  - KNOWLEDGE-semantic-embeddings.pb (40.7 KB)
  - KNOWLEDGE-embedding-systems.pb (21.0 KB)
  - KNOWLEDGE-rag-retrieval-query-hybrid-methodology.pb (5.6 KB)
Summary context (5):
  - KNOWLEDGE-advanced-rag-fusion.pb
  ...

You> /history
  [2026-02-06T14:00:01] USER: How do I build a knowledge graph?...
  [2026-02-06T14:00:15] ASSISTANT: To build a knowledge graph with Claude...
  ...

You> /switch new-experiment
Created new session 'new-experiment'

You> /export my-export.json
Session exported to my-export.json

You> quit
Session saved. Goodbye!
```

---

## 9. Context Management

### How Token Budget Works

The agent manages a ~180K token context budget:

| Component | Allocation | Notes |
|-----------|-----------|-------|
| System prompt base | ~2K tokens | Role, expertise, response style |
| Full playbooks (top 3) | ~30-45K tokens | Complete content, 15KB max each |
| Summary playbooks (up to 8) | ~2-4K tokens | Title + sections list |
| Conversation history | ~20-40K tokens | Last 20 messages from session |
| User query | Variable | Current question |
| **Response budget** | **8K tokens** | Max output per response |

### Smart Loading Strategy

```
Query: "How do I optimize costs for my RAG pipeline?"

Keyword matches:
  "cost"         -> FOUNDATION-cost-optimization.pb       (score: 2.0)
  "rag"          -> KNOWLEDGE-advanced-rag-fusion.pb       (score: 2.0)
  "optimize"     -> REASONING-meta-optimization.pb         (score: 1.0)
  "pipeline"     -> (partial match in summaries)           (score: 0.3)

Result:
  FULL:    cost-optimization, advanced-rag-fusion, meta-optimization
  SUMMARY: haiku-delegation, context-window-mgmt, embedding-systems, ...
```

### Conversation History Windowing

- Last **20 messages** are included for context continuity
- Older messages are preserved in SQLite but not sent to the API
- Token estimate is tracked per message for budget awareness
- Use `/stats` to see your current token usage

---

## 10. Cross-Provider Translation

A core use case: translating between Claude and Gemini concepts.

### Example Questions for Translation

```bash
# API differences
python3 sonnet-agent.py --ask "What's the Gemini equivalent of Claude's prompt caching?"

# Architecture translation
python3 sonnet-agent.py --ask "I built a KG with Claude. How do I replicate it in Gemini CLI?"

# Cost comparison
python3 sonnet-agent.py --ask "Compare Claude Sonnet vs Gemini 2.5 Flash for entity extraction"

# Concept mapping
python3 sonnet-agent.py --ask "How does extended thinking in Claude map to Gemini's thinking mode?"
```

### Common Translations

| Claude Concept | Gemini Equivalent |
|---------------|-------------------|
| Prompt caching (`cache_control`) | Context caching API |
| Extended thinking | Thinking mode (`thinkingConfig`) |
| System prompt | `system_instruction` |
| Tool use / function calling | Function calling (`tools`) |
| Structured output (JSON mode) | `response_mime_type: application/json` |
| Batch API | Batch prediction API |
| Citations | Google Search grounding |

The agent knows these mappings deeply from its playbook knowledge base.

---

## 11. Configuration

### Model Selection

Default model: `claude-sonnet-4-5-20250929`

```bash
# Use a different Sonnet version
python3 sonnet-agent.py --chat --model claude-sonnet-4-5-20250929

# Use Haiku for cheaper queries
python3 sonnet-agent.py --ask "Quick question" --model claude-haiku-4-5-20251001

# Use Opus for complex analysis
python3 sonnet-agent.py --ask "Deep analysis needed" --model claude-opus-4-6
```

### Custom Playbook Directory

```bash
# Command line
python3 sonnet-agent.py --playbooks --pb-dir /my/custom/playbooks/

# Environment variable
export FORGE_AI_PB_DIR="/my/custom/playbooks/"
```

The agent looks for `.pb` files matching the target playbook filenames. If some aren't found, it warns but continues with what's available.

### Custom Database Path

```bash
# Command line
python3 sonnet-agent.py --chat --db-path /path/to/my-conversations.db

# Environment variable
export FORGE_AI_DB="/path/to/my-conversations.db"
```

---

## 12. Examples & Use Cases

### Use Case 1: Building a Knowledge Graph

```bash
python3 sonnet-agent.py --chat --context "kg-build"
```

```
You> I have 500 lines of API documentation. How should I extract entities for a KG?

Sonnet> Based on KNOWLEDGE-graph-engineering.pb, here's the systematic approach:
        1. Define your schema first (node types, edge types)
        2. Use structured extraction prompts...
        [detailed response with code examples]

You> What SQLite schema should I use?

Sonnet> Here's the proven schema from FORGE-AI methodology:
        CREATE TABLE nodes (...)
        CREATE TABLE edges (...)
        [complete schema with indexes]

You> How do I validate the extracted entities?

Sonnet> See KNOWLEDGE-perception-enhancement.pb for validation patterns...
```

### Use Case 2: Gemini CLI Integration

```bash
# From Gemini CLI, call the Sonnet agent for Claude expertise
python3 sonnet-agent.py --ask "How would I implement prompt caching in Gemini? In Claude it uses cache_control ephemeral" --context "gemini-migration"
```

### Use Case 3: Cost Optimization Analysis

```bash
python3 sonnet-agent.py --ask "I'm making 1000 API calls/day with 50KB system prompts. How do I reduce costs?" --context "cost-analysis"
```

### Use Case 4: Scripted Workflows

```bash
# Extract an answer and pipe to a file
python3 sonnet-agent.py --ask "Generate a SQLite schema for a technology KG" -o schema.sql

# Use in a shell script
ANSWER=$(python3 sonnet-agent.py --ask "What's the best model for entity extraction?")
echo "$ANSWER" >> research-notes.txt
```

### Use Case 5: Multi-Project Management

```bash
# Project A: KG construction
python3 sonnet-agent.py --chat --context "project-a-kg"

# Project B: RAG pipeline
python3 sonnet-agent.py --chat --context "project-b-rag"

# Project C: Agent architecture
python3 sonnet-agent.py --chat --context "project-c-agents"

# See all projects
python3 sonnet-agent.py --sessions
```

---

## 13. Architecture

### System Overview

```
                    +-----------------------+
                    |    CLI Entry Point     |
                    |   (argparse + modes)   |
                    +-----------+-----------+
                                |
              +-----------------+-----------------+
              |                 |                 |
        +-----v-----+   +------v------+   +------v------+
        | --ask mode |   | --chat mode |   |  Info modes  |
        | (one-shot) |   | (interactive)|  | (no API)    |
        +-----+-----+   +------+------+   +------+------+
              |                 |                 |
              +--------+--------+     +-----------+-----------+
                       |              |           |           |
                +------v------+  --playbooks --sessions  --relevant
                | SonnetAgent |
                +------+------+
                       |
         +-------------+-------------+
         |             |             |
   +-----v-----+ +----v----+ +-----v-----+
   | Anthropic  | |Playbook | |Conversation|
   |  Client    | | Loader  | |    DB      |
   | (requests) | | (.pb)   | | (SQLite)   |
   +-----------+ +---------+ +-----------+
         |             |             |
   Anthropic API  26 .pb files  ~/.forge-ai/
   (REST POST)    (743 KB)     sonnet-agent.db
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| `AnthropicClient` | sonnet-agent.py | Lightweight REST client (no SDK) |
| `ConversationDB` | sonnet-agent.py | SQLite persistence layer |
| `PlaybookLoader` | sonnet-agent.py | .pb file parser + topic relevance engine |
| `SonnetAgent` | sonnet-agent.py | Core agent orchestrating all components |

### Database Schema

```sql
-- Sessions: conversation containers
sessions (
    id TEXT PRIMARY KEY,       -- 16-char hash
    name TEXT NOT NULL,        -- human-readable name
    created_at TEXT,
    updated_at TEXT,
    message_count INTEGER,
    summary TEXT,
    metadata TEXT               -- JSON blob
)

-- Messages: conversation history
messages (
    id INTEGER PRIMARY KEY,
    session_id TEXT,            -- FK to sessions
    role TEXT,                  -- 'user' | 'assistant' | 'system'
    content TEXT,
    timestamp TEXT,
    token_estimate INTEGER,    -- rough token count
    playbooks_used TEXT         -- JSON array of filenames
)

-- Playbook cache: metadata for loaded playbooks
playbook_cache (
    filename TEXT PRIMARY KEY,
    category TEXT,
    title TEXT,
    summary TEXT,
    keywords TEXT,              -- JSON array
    char_count INTEGER,
    content_hash TEXT,
    loaded_at TEXT
)
```

### API Communication

The agent calls `POST https://api.anthropic.com/v1/messages` directly:

```
Headers:
  x-api-key: <your key>
  anthropic-version: 2023-06-01
  content-type: application/json

Body:
  model: claude-sonnet-4-5-20250929
  max_tokens: 8192
  system: [{ type: "text", text: "<system prompt + playbooks>",
             cache_control: { type: "ephemeral" } }]
  messages: [<conversation history + current query>]
```

Prompt caching is enabled via `cache_control: ephemeral` on the system prompt, giving 90%+ cost reduction on follow-up messages within the same conversation.

---

## 14. Troubleshooting

### "ANTHROPIC_API_KEY not found"

```bash
# Set the key
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

# Verify it's set
echo $ANTHROPIC_API_KEY

# Or pass directly
python3 sonnet-agent.py --ask "test" --api-key "sk-ant-api03-your-key"
```

### "'requests' package not installed"

```bash
pip install requests
```

### "Playbook not found: KNOWLEDGE-xxx.pb"

The agent warns but continues. To fix:
1. Check the playbook directory: `ls /storage/emulated/0/Download/gemini-3-pro/playbooks/playbooks-v2/`
2. Use a custom directory: `--pb-dir /your/path/`
3. Some playbooks may have slightly different filenames - check available files

### "API Error (401): Invalid API key"

- Verify your key at https://console.anthropic.com
- Check it starts with `sk-ant-`
- Ensure no extra whitespace

### "API Error (429): Rate limited"

- Wait 60 seconds and retry
- Use `--model claude-haiku-4-5-20251001` for cheaper/faster queries
- Check your API tier limits

### "API Error (529): Overloaded"

- The API is temporarily busy. Wait and retry.
- Try a different model if urgent

### Database Locked

If you see SQLite lock errors:
```bash
# Check for other sonnet-agent processes
ps aux | grep sonnet-agent

# Use a different database
python3 sonnet-agent.py --chat --db-path /tmp/sonnet-test.db
```

### Large Responses Cut Off

The default max_tokens is 8192. For longer responses, the agent will naturally truncate. For very long answers, break your question into parts.

---

## 15. API Cost Reference

### Sonnet 4.5 Pricing (per 1M tokens)

| Component | Cost |
|-----------|------|
| Input tokens | $3.00 |
| Output tokens | $15.00 |
| Cache write | $3.75 |
| Cache read | $0.30 |
| Batch input | $1.50 (50% off) |
| Batch output | $7.50 (50% off) |

### Typical Query Costs

| Scenario | First Query | Subsequent (cached) |
|----------|-------------|---------------------|
| Simple question (3 playbooks) | ~$0.15-0.25 | ~$0.02-0.05 |
| Complex analysis (3 full + 8 summary) | ~$0.20-0.35 | ~$0.03-0.08 |
| Chat session (20 messages) | ~$0.30-0.50 total | Most cached |

### Cost Optimization Tips

1. **Use sessions** - Prompt caching saves 90% on the system prompt after the first message
2. **Be specific** - Targeted questions load fewer playbooks = fewer input tokens
3. **Use Haiku for simple questions** - `--model claude-haiku-4-5-20251001` is 4x cheaper
4. **Export and review** - Use `--export` to review before continuing expensive sessions
5. **Batch questions** - Multiple questions in one chat session shares the cached system prompt

---

## Appendix: File Locations

| Asset | Path |
|-------|------|
| Agent script | `NLKE/sonnet-agent.py` |
| User guide | `NLKE/SONNET-AGENT-USER-GUIDE.md` |
| Database (default) | `~/.forge-ai/sonnet-agent.db` |
| Playbooks (default) | `/storage/emulated/0/Download/gemini-3-pro/playbooks/playbooks-v2/` |
| 26 target playbooks | 9 KNOWLEDGE + 7 REASONING + 5 AGENT + 5 FOUNDATION |

---

*FORGE-AI Sonnet Agent v1.0.0 | NLKE Phase 8.5 | February 6, 2026*
