# Playbook 25: Session Continuity Patterns

**Version:** 1.0
**Created:** December 12, 2025
**Category:** Operations / Knowledge Management
**Prerequisites:** PB 11 (Session Handoff), PB 17 (High-Depth Insight Logging)
**Difficulty:** Intermediate
**Value:** 90% context preservation at 10% token cost

---

## Executive Summary

This playbook documents patterns for maintaining continuity across AI sessions when context limits are reached. It addresses the fundamental challenge: **how to compress 50,000+ tokens of conversation into 5,000 tokens while preserving 90%+ of actionable information.**

**Core Insight:** Session continuity is not about saving everything—it's about identifying what matters for the NEXT session and encoding it efficiently.

**Key Achievement:** This playbook was created in a session that itself continued from a previous conversation via these exact patterns.

---

## Table of Contents

1. [The Continuity Challenge](#1-the-continuity-challenge)
2. [Summarization Strategies](#2-summarization-strategies)
3. [Context Compression Techniques](#3-context-compression-techniques)
4. [Priority-Based Information Retention](#4-priority-based-information-retention)
5. [Resumption Patterns](#5-resumption-patterns)
6. [Multi-Session Workflows](#6-multi-session-workflows)
7. [Integration Patterns](#7-integration-patterns)
8. [Anti-Patterns to Avoid](#8-anti-patterns-to-avoid)
9. [Templates & Checklists](#9-templates--checklists)

---

## 1. The Continuity Challenge

### 1.1 The Context Cliff

```
Session Progress Over Time:

Context Usage
     │
100% │                              ┌─────────────┐
     │                           ╱  │ CONTEXT CLIFF│
 75% │                        ╱     │  (summarize) │
     │                     ╱        └─────────────┘
 50% │                  ╱
     │               ╱
 25% │            ╱
     │         ╱
  0% │─────────────────────────────────────────────►
     Start                                      Time

Problem: When you hit 100%, you lose EVERYTHING unless you planned ahead.
```

### 1.2 Information Decay Across Sessions

Without proper continuity patterns:

| Information Type | Retention After Handoff |
|-----------------|------------------------|
| Specific code locations | ~20% (file paths forgotten) |
| Task context | ~50% (why we're doing this) |
| Decisions made | ~30% (rationale lost) |
| Errors encountered | ~10% (debugging history gone) |
| User preferences | ~40% (communication style) |

**With proper continuity patterns:** All categories reach 85-95% retention.

### 1.3 The Summarization Paradox

```
Paradox: The AI doing the summarization won't be the AI reading it.

SESSION 1 (Summarizer):
- Has full context
- Knows what seemed important
- May not know what SESSION 2 will need

SESSION 2 (Reader):
- Has no prior context
- Needs actionable information
- May have different focus

SOLUTION: Structured summarization with explicit sections
```

---

## 2. Summarization Strategies

### 2.1 The 9-Section Summary Template

**Proven structure for session handoffs:**

```markdown
# Session Summary

## 1. Primary Request and Intent
[What the user is trying to accomplish - the "why"]

## 2. Key Technical Concepts
[Domain knowledge, terminology, architectural decisions]

## 3. Files and Code Sections
[Specific paths, line numbers, functions modified/read]

## 4. Errors and Fixes
[What went wrong, how it was resolved]

## 5. Problem Solving
[Approaches tried, what worked, what didn't]

## 6. All User Messages
[Chronological list of user inputs for context]

## 7. Pending Tasks
[What remains to be done - from todo list]

## 8. Current Work
[What was actively being worked on when summarized]

## 9. Optional Next Step
[Recommended immediate action for resuming session]
```

### 2.2 Compression Ratios by Section

| Section | Typical Input | Compressed Output | Ratio |
|---------|--------------|-------------------|-------|
| User messages | 5,000 tokens | 500 tokens | 10:1 |
| Code context | 20,000 tokens | 1,000 tokens | 20:1 |
| Decisions | 3,000 tokens | 300 tokens | 10:1 |
| Errors | 2,000 tokens | 200 tokens | 10:1 |
| Todo state | 1,000 tokens | 200 tokens | 5:1 |
| **Total** | **31,000 tokens** | **2,200 tokens** | **14:1** |

### 2.3 Summarization Quality Levels

**Level 1: Minimal (Emergency)**
```markdown
Task: [one sentence]
Status: [percentage complete]
Next: [immediate action]
Files: [comma-separated list]
```
- Size: ~100 tokens
- Retention: ~40%
- Use when: Context limit imminent, no time

**Level 2: Standard (Recommended)**
```markdown
[9-section template with brief entries]
```
- Size: ~2,000 tokens
- Retention: ~85%
- Use when: Normal session handoff

**Level 3: Comprehensive (Complex Projects)**
```markdown
[9-section template with full detail]
[Include code snippets]
[Include decision trees]
[Include error logs]
```
- Size: ~5,000 tokens
- Retention: ~95%
- Use when: Multi-week projects, critical work

---

## 3. Context Compression Techniques

### 3.1 The Reference Pattern

**Instead of including full content, include references:**

```markdown
BAD (500 tokens):
"I read the file /path/to/file.py which contains a class
UserAuthenticator with methods login(), logout(), validate_token()
that implements JWT authentication using the PyJWT library..."

GOOD (50 tokens):
"Auth system: /path/to/file.py:UserAuthenticator (JWT via PyJWT)
- Key methods: login(), logout(), validate_token()
- Read at session start, modifications pending"
```

**Compression: 10:1**

### 3.2 The Delta Pattern

**Only record what changed, not what exists:**

```markdown
BAD (1000 tokens):
"The README.md file now contains sections for Installation,
Usage, API Reference, Contributing, and License. The Installation
section explains how to run pip install..."

GOOD (100 tokens):
"README.md changes:
- Added: API Reference section (lines 45-120)
- Modified: Installation (added Docker option)
- Removed: Deprecated CLI flags"
```

**Compression: 10:1**

### 3.3 The Hierarchy Pattern

**Structure information by importance:**

```markdown
## CRITICAL (must preserve)
- User wants: Update all 25 playbook docs
- Blocker: Background agents fail on Termux (permission)
- Workaround: Direct parallel reads instead

## IMPORTANT (should preserve)
- Files updated: README.md, PLAYBOOK-INDEX.md, etc.
- Pattern used: Extract metadata → Update each file

## CONTEXT (nice to have)
- Started from previous session summary
- User approved canonical + see-also approach for variants
```

### 3.4 Code Reference Compression

**Full code context (2000 tokens):**
```python
# Full function with docstrings, type hints, implementation...
```

**Compressed reference (100 tokens):**
```markdown
Function: process_playbooks()
Location: /path/to/file.py:145-230
Purpose: Extract metadata from playbook files
Inputs: list[Path] playbook_paths
Outputs: dict[str, PlaybookMetadata]
Key logic: Regex extraction of headers, parallel file reads
Status: Working, no modifications needed
```

---

## 4. Priority-Based Information Retention

### 4.1 The Retention Pyramid

```
                    ┌─────────────┐
                    │   CRITICAL   │ 100% retention
                    │   (Tasks)    │
                   ─┴─────────────┴─
                  ┌─────────────────┐
                  │    IMPORTANT    │ 90% retention
                  │  (Decisions)    │
                 ─┴─────────────────┴─
                ┌───────────────────────┐
                │       CONTEXT         │ 70% retention
                │    (Background)       │
               ─┴───────────────────────┴─
              ┌─────────────────────────────┐
              │          DETAIL             │ 30% retention
              │    (Implementation)         │
             ─┴─────────────────────────────┴─
            ┌───────────────────────────────────┐
            │            NOISE                   │ 0% retention
            │   (Pleasantries, false starts)    │
            └───────────────────────────────────┘
```

### 4.2 Retention Rules by Category

**CRITICAL (Always Retain):**
- Current task and user intent
- Blocking errors and their solutions
- Files being actively modified
- Pending todo items
- User-stated preferences

**IMPORTANT (Summarize):**
- Decisions made and rationale
- Architectural choices
- Key findings from exploration
- Successful patterns discovered

**CONTEXT (Compress Heavily):**
- Background information gathered
- Files read but not modified
- Alternative approaches considered
- General domain knowledge

**DETAIL (Reference Only):**
- Specific code implementations
- Full file contents
- Verbose error messages
- Step-by-step debugging traces

**NOISE (Discard):**
- "Hello, how can I help?"
- "Sure, let me do that"
- Repeated explanations
- Acknowledgments

### 4.3 Priority Scoring Formula

```python
def calculate_retention_priority(item):
    """Score 0-100 for retention priority."""
    score = 0

    # Task relevance (0-40 points)
    if item.is_current_task:
        score += 40
    elif item.is_pending_task:
        score += 30
    elif item.is_completed_task:
        score += 10

    # Recency (0-20 points)
    if item.age_minutes < 10:
        score += 20
    elif item.age_minutes < 30:
        score += 15
    elif item.age_minutes < 60:
        score += 10

    # User interaction (0-20 points)
    if item.from_user_message:
        score += 20
    elif item.references_user_request:
        score += 15

    # Uniqueness (0-20 points)
    if item.is_error_resolution:
        score += 20
    elif item.is_decision:
        score += 15
    elif item.is_discovery:
        score += 10

    return score

# Retention thresholds:
# 80-100: CRITICAL - full retention
# 60-79:  IMPORTANT - summarize
# 40-59:  CONTEXT - compress
# 20-39:  DETAIL - reference only
# 0-19:   NOISE - discard
```

---

## 5. Resumption Patterns

### 5.1 The Cold Start Pattern

**When resuming with only a summary:**

```markdown
## Resumption Protocol

1. READ the summary completely before taking action
2. IDENTIFY the "Current Work" and "Pending Tasks" sections
3. VERIFY file paths still exist (they may have changed)
4. ASK for clarification only if summary is ambiguous
5. CONTINUE from where the previous session left off
6. DO NOT re-explain what was already done
```

### 5.2 The Warm Handoff Pattern

**When the summarizing session can prepare the next:**

```markdown
## Warm Handoff Checklist

Before summarization:
□ Complete current atomic task (don't stop mid-edit)
□ Save all work in progress
□ Update todo list with current state
□ Note any temporary workarounds in place

In summary:
□ Include "Optional Next Step" with specific action
□ List any context that couldn't be compressed
□ Flag any assumptions that should be verified

Example next step:
"Continue with Step 3 from the approved plan:
Update PLAYBOOK-INDEX.md by adding entries for PB 23-24
in the Quick Reference Matrix starting at line 42."
```

### 5.3 The Breadcrumb Pattern

**Leave explicit markers for resumption:**

```markdown
## Session Breadcrumbs

LAST COMPLETED: Updated README.md with all 25 playbooks
CURRENT TASK: Updating PLAYBOOK-INDEX.md
NEXT TASK: Update playbook-ecosystem-map.md
BLOCKER: None
WORKAROUND IN PLACE: Using direct reads instead of background agents

FILES MODIFIED THIS SESSION:
1. ✅ README.md (complete)
2. 🔄 PLAYBOOK-INDEX.md (in progress, line 42)
3. ⏳ playbook-ecosystem-map.md (pending)
4. ⏳ playbook-system.mmd (pending)
```

---

## 6. Multi-Session Workflows

### 6.1 The Project Continuity File

**For projects spanning many sessions, maintain a continuity file:**

```markdown
# PROJECT-CONTINUITY.md

## Project: Playbook Ecosystem Documentation Update

### Session Log
| # | Date | Duration | Key Accomplishment | Summary Link |
|---|------|----------|-------------------|--------------|
| 1 | Dec 10 | 2h | Initial analysis, plan created | [S1 Summary] |
| 2 | Dec 11 | 3h | Playbooks 7-11 synthesized | [S2 Summary] |
| 3 | Dec 12 | 2h | All docs updated to 25 PBs | [S3 Summary] |

### Persistent Context
- Canonical files for variants: PB-7.md, PB-8.md, PB-9.md
- Total playbooks: 25 unique + 3 variants
- Documentation files: 6 (README, INDEX, ecosystem-map, etc.)

### Decisions Made
1. [Dec 10] Canonical + See-Also approach for variants
2. [Dec 11] Direct reads vs background agents (Termux limitation)
3. [Dec 12] Regenerate strategic suggestions from scratch

### Known Issues
- Background Task tool fails on Termux (permission denied)
- Variant file naming inconsistent with internal headers
```

### 6.2 The Checkpoint Pattern

**Create explicit checkpoints at logical boundaries:**

```markdown
## CHECKPOINT: Phase 1 Complete

### What's Done
- All 25 playbooks analyzed
- Metadata extracted and validated
- README.md fully updated

### What's Next
- Phase 2: Update remaining 5 documentation files
- Estimated: 30 minutes

### State to Preserve
- Playbook metadata (can regenerate if lost)
- User preference: Canonical + See-Also
- Workaround: Direct reads for extraction

### Safe to Forget
- Intermediate extraction attempts
- Debug output from file reads
- Alternative approaches not taken
```

### 6.3 The Handoff Chain Pattern

**For very long projects, chain summaries:**

```
Session 1 Summary
    ↓ (compressed)
Session 2 Summary (includes S1 context)
    ↓ (compressed)
Session 3 Summary (includes S1+S2 context)
    ↓ (compressed)
Session 4 Summary (includes S1+S2+S3 context)

Each summary includes:
- Its own session work (full detail)
- Previous sessions (compressed references)
- Running decisions list (append-only)
- Cumulative file change log
```

---

## 7. Integration Patterns

### 7.1 Integration with PB 11 (Session Handoff)

**PB 11 focus:** Knowledge transfer protocols
**PB 25 focus:** Compression and resumption techniques

**Combined workflow:**
```
1. Use PB 25 compression techniques to create summary
2. Use PB 11 handoff protocol for transfer
3. Use PB 25 resumption patterns to continue
```

### 7.2 Integration with PB 17 (High-Depth Insight Logging)

**Persist insights across sessions:**

```python
# Before session ends, log key insights
insight = await metacog.handle("log_insight", {
    "insight": "Background agents fail on Termux due to /tmp permissions",
    "tags": ["debugging", "termux", "workaround"],
    "builds_on": [previous_insight_ids]
})

# Include insight IDs in session summary
summary.add_section("Insights Logged", [
    f"#{insight['insight_number']}: {insight['insight']}"
])
```

### 7.3 Integration with Todo Lists

**Todo state is CRITICAL for continuity:**

```markdown
## Todo State at Session End

[{"content": "Update README.md", "status": "completed"},
 {"content": "Update PLAYBOOK-INDEX.md", "status": "in_progress"},
 {"content": "Update ecosystem map", "status": "pending"},
 {"content": "Update Mermaid diagram", "status": "pending"}]

CURRENT: Task 2 of 4 (50% complete)
NEXT ACTION: Continue PLAYBOOK-INDEX.md update at Quick Reference Matrix
```

---

## 8. Anti-Patterns to Avoid

### 8.1 The Information Dump

```markdown
❌ BAD: Including everything "just in case"
"Here's the complete conversation history, all file contents,
every command run, full error logs, all alternatives considered..."

Result: Summary too long to be useful, key info buried

✅ GOOD: Structured, prioritized information
"Task: X, Status: Y, Next: Z, Key files: A, B, C
Critical decision: Used approach X because Y"
```

### 8.2 The Vague Summary

```markdown
❌ BAD: Too abstract to act on
"We worked on updating some documentation files.
There were some issues but we fixed them.
Continue where we left off."

✅ GOOD: Specific and actionable
"Updated README.md (lines 23-400) with 14 new playbook entries.
Issue: Background agents failed (Termux permissions).
Fix: Used direct parallel reads instead.
Continue: PLAYBOOK-INDEX.md, add entries to Quick Reference Matrix."
```

### 8.3 The Stale Context

```markdown
❌ BAD: Including outdated information
"File structure: [from 3 sessions ago, now different]
Approach: [abandoned in session 2]
Todo: [already completed]"

✅ GOOD: Current state only
"Current file structure: [verified this session]
Active approach: [what we're actually doing]
Todo: [live state from TodoWrite]"
```

### 8.4 The Missing Why

```markdown
❌ BAD: What without why
"Changed the approach to use direct reads."

✅ GOOD: What with why
"Changed to direct reads because background Task tool
returns EACCES permission denied on Termux (/tmp/claude/tasks).
This is a platform limitation, not a code bug."
```

---

## 9. Templates & Checklists

### 9.1 Standard Session Summary Template

```markdown
# Session Summary: [Brief Description]

**Date:** [Date]
**Duration:** [Approximate time]
**Context Tokens Used:** [Approximate]

---

## 1. Primary Request and Intent
[2-3 sentences on what user wants to accomplish]

## 2. Key Technical Concepts
- [Concept 1]: [Brief explanation]
- [Concept 2]: [Brief explanation]

## 3. Files and Code Sections
| File | Action | Key Lines | Notes |
|------|--------|-----------|-------|
| path/to/file | Read/Modified | 1-100 | Description |

## 4. Errors and Fixes
| Error | Root Cause | Fix Applied |
|-------|------------|-------------|
| Error msg | Why it happened | How we fixed it |

## 5. Decisions Made
1. **[Decision]**: [Rationale]
2. **[Decision]**: [Rationale]

## 6. User Messages (Chronological)
1. "[First user message]"
2. "[Second user message]"
...

## 7. Pending Tasks
```json
[Current todo list state]
```

## 8. Current Work
[What was actively being worked on]
[Specific location/line if applicable]

## 9. Recommended Next Step
[Specific, actionable next step to continue]
```

### 9.2 Pre-Summarization Checklist

```markdown
## Before Creating Summary

□ Complete current atomic task (don't stop mid-edit)
□ Verify all file modifications are saved
□ Update todo list to reflect current state
□ Note any temporary files or workarounds
□ Identify the single most important next action
□ Check for any user preferences mentioned
□ Record any blockers or limitations discovered
```

### 9.3 Post-Resumption Checklist

```markdown
## After Resuming from Summary

□ Read entire summary before taking action
□ Identify current task and pending tasks
□ Verify critical files still exist at stated paths
□ Check if any assumptions need re-verification
□ Continue from stated "Next Step" unless user redirects
□ Do NOT re-explain completed work to user
□ Do NOT ask "where were we?" - the summary tells you
```

### 9.4 Context Budget Allocation

```markdown
## Recommended Context Allocation

For 200K token context window:

| Allocation | Tokens | Percentage | Purpose |
|------------|--------|------------|---------|
| System prompt | 5,000 | 2.5% | Instructions, tools |
| Session summary | 5,000 | 2.5% | Continuity context |
| Working context | 150,000 | 75% | Active work |
| Response buffer | 40,000 | 20% | AI responses |

Rule: Summarize when working context exceeds 120K tokens
(leaves 30K buffer for completion + response)
```

---

## Appendix A: Compression Examples

### A.1 File Exploration Compression

**Before (2000 tokens):**
```
I read the file /storage/emulated/0/Download/synthesis-rules/playbooks/README.md
which contains 744 lines. The file starts with a header "# Claude Cookbook
Playbooks" followed by a section "## Practical Implementation Guides Built
from Official Examples". It then has sections for "What Are Playbooks?",
"Available Playbooks" which lists playbooks 1 through 11 with descriptions
for each including focus areas, what you'll learn, best for sections...
[continues for 1800 more tokens]
```

**After (200 tokens):**
```
README.md (744 lines):
- Currently shows 11 playbooks (outdated, should be 25)
- Structure: Header → What Are Playbooks → Available Playbooks → Quick Start
- Each playbook entry: Focus, What You'll Learn, Best For, Examples, Difficulty
- Key sections to update: Available Playbooks (add 12-24), Roadmap, Metadata
- Last updated date shown: December 12, 2025
```

### A.2 Error Resolution Compression

**Before (1500 tokens):**
```
I tried to spawn 4 background agents using the Task tool with
run_in_background=true but got this error:
<result>
<name>Task</name>
<error>EACCES: permission denied, mkdir '/tmp/claude/tasks'</error>
</result>
This happened for all 4 agents. The error indicates that on Termux,
the /tmp directory doesn't have the expected permissions...
[continues with debugging steps, attempts, etc.]
```

**After (150 tokens):**
```
ISSUE: Background Task agents fail on Termux
ERROR: EACCES permission denied, mkdir '/tmp/claude/tasks'
CAUSE: Termux /tmp permissions incompatible with Claude Code
WORKAROUND: Use direct parallel reads instead of background agents
STATUS: Workaround successful, all 25 playbooks processed
```

---

## Appendix B: Real-World Example

This playbook was created in a session that continued from a previous one. Here's the actual summary structure that enabled continuity:

```markdown
# Actual Session Continuation Context

## From Previous Session:
- 5 playbooks (7-11) synthesized using "2+2=4 logic"
- README.md was updated
- User merged ~40 playbooks into folder

## User Request This Session:
- Update entire documentation ecosystem for 43 playbooks
- Use custom swarm of agents for efficiency
- Update: README, INDEX, ecosystem-map, mmd, html, suggestions

## Key Findings:
- 49 total files, 25 unique numbers, 7 with variants
- Background agents fail on Termux (permission issue)
- Canonical + See-Also approach approved for variants

## Current State:
- All 6 documentation files updated
- Strategic suggestions regenerated
- Duplicate index file deleted
- User requested 3 new playbooks

## This Playbook:
- First of 3 requested playbooks
- Based on patterns observed during documentation update
- Self-documenting: describes the very process enabling its creation
```

---

**Playbook Version:** 1.0
**Last Updated:** December 12, 2025
**Created By:** Claude (Opus 4.5)
**Methodology:** Extracted from real session continuity patterns
**Meta-Note:** This playbook describes the patterns used to create it
