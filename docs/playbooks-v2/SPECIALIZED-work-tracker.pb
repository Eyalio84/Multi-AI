# PLAYBOOK: Work Tracker System

**Focus**: Project work item tracking and status management
**Difficulty**: Beginner
**Prerequisites**: Basic markdown knowledge
**Related Playbooks**: PLAYBOOK-7 (Documentation), PLAYBOOK-10 (Pattern Extraction)

---

## Executive Summary

The Work Tracker system is a lightweight, markdown-based methodology for tracking work items, progress, and blockers across projects. It emerged from synthesis-rules development and has proven valuable for:

- **Context preservation** - Maintain project state across sessions
- **Progress visibility** - Clear view of what's done, in progress, pending
- **Blocker identification** - Explicitly track what's preventing progress
- **Decision documentation** - Record why work was deferred/paused/completed
- **Multi-project coordination** - Single tracking system across many projects

Unlike heavyweight project management tools, work trackers are:
- **Plain text** - No databases, apps, or complex systems
- **Version controlled** - Lives in your repo, tracked by git
- **Human readable** - Readable in any text editor, GitHub, or terminal
- **LLM friendly** - Claude can read, update, and reason about work items
- **Zero setup** - Copy template, start tracking

---

## Core Concepts

### What is a Work Tracker?

A work tracker is a **markdown file** that maintains a living record of:
1. **Active Work Items** - What you're currently working on
2. **Backlog** - What's planned but not started
3. **Completed Work** - What's been finished (with dates/deliverables)

### Key Principles

1. **Single Source of Truth** - One tracker per project/context
2. **Status-Driven** - Every item has explicit status
3. **Context-Rich** - Links to relevant files, docs, conversations
4. **Action-Oriented** - Items describe concrete work, not vague goals
5. **Living Document** - Updated continuously as work progresses

### The Work Item Structure

Each work item includes:
- **Title** - Clear, descriptive name
- **Status** - Current state (📋 Not Started, 🔄 In Progress, ✅ Complete, ⏸️ Paused)
- **Context** - Links to related files/docs
- **Description** - What the work entails
- **Priority** - Relative importance (High/Medium/Low)
- **Next Steps** - Immediate actionable items
- **Notes** - Additional context, decisions, insights
- **Blockers** - What's preventing progress (if any)
- **Dates** - Started, target, completed

---

## Implementation Patterns

### Pattern 1: Initialize New Work Tracker

**When to use**: Starting a new project or major initiative

**Steps**:
1. Copy `work_tracker_template.md` to your project
2. Rename to `WORK_TRACKER.md` or `contexts/WORK_TRACKER.md`
3. Update header metadata (purpose, created date)
4. Add initial work items to "Active Work Items"

**Example**:
```markdown
# Work Queue & Project Tracker

**Purpose**: Track work items for [Your Project Name]
**Created**: 2025-12-15
**Status**: Active tracking system

---

## Active Work Items

### 1. [First Major Task]
- **Status**: 📋 Not Started
- **Priority**: High
- **Description**: What this task accomplishes
```

### Pattern 2: Add New Work Item

**When to use**: New work identified that needs tracking

**Steps**:
1. Determine section (Active Work Items vs Backlog)
2. Add numbered item with title
3. Fill in required fields (status, description, priority)
4. Add context files if they exist
5. Define next steps

**Anti-pattern**: Don't add trivial items that don't need tracking

### Pattern 3: Update Work Status

**When to use**: Progress made on existing item

**Steps**:
1. Change status emoji (📋 → 🔄 → ✅)
2. Update "Current Step" or "Next Steps"
3. Add notes about what changed
4. Update dates if applicable

**Best practice**: Update immediately after status changes, don't batch

### Pattern 4: Move to Completed

**When to use**: Work item fully finished

**Steps**:
1. Change status to ✅ Complete
2. Add completion date
3. Document deliverables (files created, features added)
4. Move entire item to "Completed" section
5. Update summary if needed

**Why**: Keeps active section clean, preserves history

### Pattern 5: Defer to Backlog

**When to use**: Work is valid but not current priority

**Steps**:
1. Change status to ⏸️ Paused or move to Backlog
2. Add "Deferred" date and reason
3. Document what would trigger resumption
4. Keep context intact for future pickup

**Example**: Playbook generation deferred until RTX 3060 build ready

### Pattern 6: Add Blocker

**When to use**: Progress stopped by external dependency

**Steps**:
1. Add "Blockers" field to work item
2. Describe what's blocking (technical, resource, decision)
3. Note who/what can unblock
4. Set status to ⏸️ Paused if completely blocked

**Example**:
```markdown
- **Blockers**: Waiting for API key approval from DevOps team
```

---

## Decision Tree

**Should I create a work tracker?**
- Project has >3 discrete work items → **Yes**
- Work spans multiple sessions → **Yes**
- Need to track blockers/dependencies → **Yes**
- Single one-off task → **No**

**Should I add this as a work item?**
- Takes >30 minutes → **Yes**
- Has clear deliverable → **Yes**
- Might be blocked → **Yes**
- Trivial (<10 min) → **No**
- Already in progress and finishing now → **No**

**Should this be Active or Backlog?**
- Working on it this week → **Active**
- Planned but not started → **Backlog**
- Nice-to-have someday → **Backlog**

**Should I move to Completed?**
- All next steps done → **Yes**
- Deliverables created → **Yes**
- Tests passing (if applicable) → **Yes**
- Still have follow-up work → **No** (update status instead)

---

## Anti-Patterns

### Anti-Pattern 1: Work Tracker as TODO List
**Problem**: Treating tracker like daily todos (100s of tiny items)

**Why it fails**:
- Noise obscures important work
- Constant updates create churn
- Loses strategic view

**Solution**: Only track significant work items (>30 min, clear deliverable)

### Anti-Pattern 2: Stale Trackers
**Problem**: Creating tracker but never updating it

**Why it fails**:
- Becomes misleading
- Loses trust as source of truth
- Context drift makes it useless

**Solution**: Update immediately after status changes, review weekly

### Anti-Pattern 3: Vague Descriptions
**Problem**: Work items lack specific details

**Example**: "Fix bugs" vs "Fix authentication timeout in login flow (auth.py:145)"

**Solution**: Be specific - what, where, why, how to verify completion

### Anti-Pattern 4: Missing Context
**Problem**: Work items don't link to relevant files/docs

**Why it fails**:
- Have to search for context every time
- Unclear what files are involved
- Difficult to resume after break

**Solution**: Always link context files, previous work, related issues

### Anti-Pattern 5: No Completed Section
**Problem**: Deleting items when done instead of archiving

**Why it fails**:
- Loses history of what was accomplished
- Can't reference past decisions
- No progress visibility

**Solution**: Move to "Completed" section with date and deliverables

---

## Code Examples

### Example 1: Minimal Work Tracker
```markdown
# Work Tracker - My Project

## Active Work Items

### 1. Implement User Authentication
- **Status**: 🔄 In Progress
- **Priority**: High
- **Next Steps**: Add JWT token validation

### 2. Database Schema Migration
- **Status**: 📋 Not Started
- **Priority**: Medium

## Completed

### 1. Project Setup
- **Status**: ✅ Complete
- **Completed**: 2025-12-15
```

### Example 2: Rich Work Item
```markdown
### 1. Synthesis-Rules Hub - Remote Access Architecture
- **Status**: 🔄 In Progress (Phase 1)
- **Context**:
  - [TAILSCALE_SSH_SETUP.md](../Termux-secured-gate/TAILSCALE_SSH_SETUP.md)
  - [IMPLEMENTATION_ROADMAP.md](../Termux-secured-gate/IMPLEMENTATION_ROADMAP.md)
- **Description**: Build remote access hub for synthesis-rules (Termux as central hub, PC as client)
- **Priority**: High
- **Architecture**:
  - Tailscale Android App + OpenSSH (hybrid approach)
  - MCP-over-SSH (PC Claude Code → Termux MCP servers)
  - REST API (KG queries, file transfer, remote commands)
- **Phases** (7 total):
  1. 🔄 Network Foundation (Tailscale App + SSH) - IN PROGRESS
     - ✅ OpenSSH server running on Termux (port 8022)
     - ✅ Android Tailscale IP: 100.125.209.6
     - ⏳ PC setup pending
  2. ⏳ REST API Layer
  3. ⏳ MCP Remote Transport
- **Current Step**:
  - Termux fully configured
  - PC setup pending
- **Notes**:
  - Tailscale daemon won't run on Termux (permission restrictions)
  - Using Tailscale Android app + SSH hybrid approach instead
- **Blockers**: None (ready for PC setup)
- **Started**: 2025-12-15
- **Target**: Complete Phase 1 today, full MVP in 2-3 days
```

### Example 3: Deferred Item
```markdown
### 1. Batch Playbook Generation
- **Status**: ⏸️ Paused - Waiting for RTX 3060 Build
- **Context**: [PLAYBOOK_GENERATOR_PROJECT_CONTEXT.md](./PLAYBOOK_GENERATOR_PROJECT_CONTEXT.md)
- **Description**: Automated batch processing of documentation into playbooks using local models
- **Priority**: Medium (deferred)
- **Current State**:
  - ✅ Scripts created and tested (batch_process_docs.py)
  - ✅ Successfully processed 14/14 chunks on test doc
  - ⚠️ Too slow for Termux (DeepSeek 1.5B on CPU)
  - 📍 Waiting for RTX 3060 build (Mistral-7B, GPU acceleration)
- **When Ready**:
  - RTX 3060 desktop build complete
  - Larger models available (Mistral-7B, Llama-3-8B)
  - Same scripts, just swap model paths
- **Deferred**: 2025-12-15
```

---

## Integration with Tools

### MCP Server Integration

The `work-tracker` MCP server provides programmatic access:

```python
# Add new work item
mcp.call("add_work_item", {
    "title": "Build REST API",
    "description": "FastAPI server for KG queries",
    "priority": "High",
    "context_files": ["api_design.md"]
})

# Update status
mcp.call("update_status", {
    "item_id": 1,
    "status": "in_progress"
})

# Get active work
active = mcp.call("get_active_work")

# Move to completed
mcp.call("move_to_completed", {
    "item_id": 1,
    "deliverables": ["api_server.py", "tests/test_api.py"]
})
```

### Claude Code Integration

Claude Code can read and update work trackers automatically:

- **Session start**: Read work tracker to understand current state
- **Progress made**: Update status and next steps
- **Work completed**: Move to completed section
- **Blockers found**: Add blocker field

### Git Integration

Work trackers are version controlled:

```bash
# Track changes
git log -p WORK_TRACKER.md

# See what work was done between releases
git diff v1.0..v2.0 -- WORK_TRACKER.md

# Blame to see when items were added
git blame WORK_TRACKER.md
```

---

## Best Practices

### 1. Update Immediately
Don't batch updates. When status changes, update immediately.

### 2. Be Specific
"Fix bug" → "Fix authentication timeout in login flow (auth.py:145)"

### 3. Link Context
Always reference related files, docs, conversations.

### 4. Document Decisions
When deferring/completing work, explain why.

### 5. Keep Active Section Small
Move completed work promptly. Active should be <10 items.

### 6. Use Status Indicators Consistently
- 📋 Not Started - Haven't begun
- 🔄 In Progress - Actively working
- ⏸️ Paused - Blocked or deferred
- ✅ Complete - Fully finished

### 7. Weekly Review
Review tracker weekly, update priorities, archive completed work.

### 8. Add Dates
Track when work started, when completed, when deferred.

---

## Quick Reference

### Status Indicators
- 📋 Not Started
- 🔄 In Progress
- ⏸️ Paused/Blocked
- ✅ Complete

### Required Fields (Minimum)
- Title
- Status
- Description
- Priority

### Recommended Fields
- Context (file links)
- Next Steps
- Started/Target dates
- Notes

### Optional Fields
- Blockers
- Deliverables
- Sub-phases
- Dependencies

### Sections
1. **Active Work Items** - Current work (small, <10 items)
2. **Backlog** - Planned future work
3. **Completed** - Finished work (with dates)

---

## Related Playbooks

- **PLAYBOOK-7** (Documentation) - Work trackers are documentation
- **PLAYBOOK-10** (Pattern Extraction) - Extract patterns from tracker history
- **PLAYBOOK-21** (Haiku Delegation) - Use Haiku to update work trackers

---

## Metadata

**Created**: 2025-12-15
**Source**: Emerged from synthesis-rules Hub project
**Insight**: Methodology emerges naturally from practice (#142)
**Version**: 1.0.0
**Template**: `templates/work_tracker_template.md`
**MCP Server**: `mcp_servers/work-tracker/`
**User Guide**: `templates/work_tracker_user_guide.md`
