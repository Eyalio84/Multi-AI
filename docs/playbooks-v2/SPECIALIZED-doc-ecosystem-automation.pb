# Playbook 26: Documentation Ecosystem Automation

**Version:** 1.0
**Date:** December 12, 2025
**Focus:** Automating documentation synchronization, validation, and maintenance across playbook ecosystems
**Prerequisites:** PB-0 (Playbook System), PB-11 (Parallel Agent Orchestration), PB-21 (Haiku Delegation)
**Difficulty:** Intermediate
**Time Investment:** 4-6 hours to implement core patterns

---

## Table of Contents

1. [The Documentation Synchronization Challenge](#1-the-documentation-synchronization-challenge)
2. [Documentation Ecosystem Architecture](#2-documentation-ecosystem-architecture)
3. [Metadata Extraction Patterns](#3-metadata-extraction-patterns)
4. [Template-Driven Updates](#4-template-driven-updates)
5. [Cross-Reference Validation](#5-cross-reference-validation)
6. [Automated Synchronization Workflows](#6-automated-synchronization-workflows)
7. [Multi-File Update Orchestration](#7-multi-file-update-orchestration)
8. [Integration Patterns](#8-integration-patterns)
9. [Anti-Patterns to Avoid](#9-anti-patterns-to-avoid)
10. [Templates and Checklists](#10-templates-and-checklists)

---

## 1. The Documentation Synchronization Challenge

### The Problem

Documentation ecosystems naturally drift out of sync:

```
Initial State (t=0):
├── README.md         → "12 playbooks"
├── INDEX.md          → "12 playbooks"
├── ecosystem-map.md  → "12 playbooks"
└── guide.html        → "12 playbooks"

After Adding 13 Playbooks (t=1):
├── README.md         → "12 playbooks" ❌ STALE
├── INDEX.md          → "12 playbooks" ❌ STALE
├── ecosystem-map.md  → "12 playbooks" ❌ STALE
├── guide.html        → "12 playbooks" ❌ STALE
└── playbooks/        → 25 actual files ✓
```

### Drift Categories

| Category | Example | Detection Method |
|----------|---------|------------------|
| **Count Drift** | "12 playbooks" when 25 exist | File counting vs. stated count |
| **Reference Drift** | Links to renamed/deleted files | Link validation |
| **Metadata Drift** | Wrong title/description | Content extraction vs. stated |
| **Structure Drift** | Missing from index/map | Inventory comparison |
| **Version Drift** | Outdated version numbers | Timestamp comparison |

### Cost of Manual Synchronization

```
Manual Update Time:
├── README.md         → 30 min
├── INDEX.md          → 45 min
├── ecosystem-map.md  → 30 min
├── guide.html        → 20 min
├── system.mmd        → 15 min
└── suggestions.md    → 60 min
────────────────────────────────
Total: ~3.5 hours per update cycle

Automated Update Time:
├── Metadata extraction → 2 min
├── Template rendering  → 1 min
├── Validation          → 1 min
└── File writes         → 1 min
────────────────────────────────
Total: ~5 minutes (42x faster)
```

---

## 2. Documentation Ecosystem Architecture

### File Type Classification

```
Documentation Ecosystem
├── Source Files (authoritative)
│   └── PLAYBOOK-*.md           # Primary content
│
├── Index Files (derived)
│   ├── README.md               # Entry point
│   ├── PLAYBOOK-INDEX.md       # Quick reference
│   └── playbooks-index.md      # Duplicate (merge/delete)
│
├── Visual Files (derived)
│   ├── ecosystem-map.md        # ASCII diagrams
│   ├── system.mmd              # Mermaid flowchart
│   └── guide.html              # Interactive viewer
│
└── Planning Files (regenerated)
    └── STRATEGIC-SUGGESTIONS.md # Gap analysis
```

### Dependency Graph

```
                    Source Files
                         │
                         ▼
              ┌──────────────────────┐
              │ Metadata Extraction  │
              │   (Title, Focus,     │
              │    Prerequisites)    │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │  Index   │   │  Visual  │   │ Planning │
   │  Files   │   │  Files   │   │  Files   │
   └──────────┘   └──────────┘   └──────────┘
```

### Update Propagation Rules

```python
# When source files change:
IF playbook_added OR playbook_removed OR playbook_renamed:
    UPDATE: README.md           # Count, list
    UPDATE: PLAYBOOK-INDEX.md   # Full reference
    UPDATE: ecosystem-map.md    # Diagrams
    UPDATE: system.mmd          # Flowchart
    UPDATE: guide.html          # Cards
    REGENERATE: suggestions.md  # Gap analysis

IF playbook_content_changed:
    UPDATE: PLAYBOOK-INDEX.md   # If title/focus changed
    UPDATE: README.md           # If description changed

IF playbook_prerequisites_changed:
    UPDATE: system.mmd          # Dependency edges
    UPDATE: ecosystem-map.md    # Layer assignments
```

---

## 3. Metadata Extraction Patterns

### Standard Playbook Header Format

```markdown
# Playbook N: Title Here

**Version:** X.Y
**Date:** Month Day, Year
**Focus:** One-line description
**Prerequisites:** PB-X, PB-Y, PB-Z
**Difficulty:** Beginner/Intermediate/Advanced
**Time Investment:** X-Y hours/days
```

### Extraction Regex Patterns

```python
EXTRACTION_PATTERNS = {
    "title": r'^# Playbook (\d+): (.+)$',
    "version": r'\*\*Version:\*\*\s*(.+)',
    "date": r'\*\*Date:\*\*\s*(.+)',
    "focus": r'\*\*Focus:\*\*\s*(.+)',
    "prerequisites": r'\*\*Prerequisites:\*\*\s*(.+)',
    "difficulty": r'\*\*Difficulty:\*\*\s*(.+)',
    "time": r'\*\*Time Investment:\*\*\s*(.+)',
}

def extract_metadata(content: str) -> dict:
    """Extract structured metadata from playbook content."""
    metadata = {}
    for key, pattern in EXTRACTION_PATTERNS.items():
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            metadata[key] = match.group(1).strip()
    return metadata
```

### Section Extraction

```python
def extract_sections(content: str) -> list[str]:
    """Extract top-level section headers."""
    pattern = r'^## \d+\. (.+)$'
    return re.findall(pattern, content, re.MULTILINE)

# Example output:
# [
#   "The Documentation Synchronization Challenge",
#   "Documentation Ecosystem Architecture",
#   "Metadata Extraction Patterns",
#   ...
# ]
```

### Prerequisite Parsing

```python
def parse_prerequisites(prereq_string: str) -> list[str]:
    """Parse prerequisite string into list of playbook IDs."""
    # Handle formats:
    # "PB-1, PB-2, PB-3"
    # "PB-1 (Cost), PB-2 (Thinking)"
    # "None"

    if prereq_string.lower() == "none":
        return []

    pattern = r'PB-?(\d+)'
    matches = re.findall(pattern, prereq_string)
    return [f"PB-{m}" for m in matches]
```

### Batch Metadata Extraction

```python
def extract_all_playbook_metadata(playbook_dir: Path) -> dict:
    """Extract metadata from all playbooks in parallel batches."""

    playbooks = sorted(playbook_dir.glob("PLAYBOOK-*.md"))

    metadata_registry = {}

    for playbook_path in playbooks:
        content = playbook_path.read_text()
        metadata = extract_metadata(content)
        metadata["file"] = playbook_path.name
        metadata["sections"] = extract_sections(content)
        metadata["line_count"] = len(content.splitlines())

        # Extract playbook number
        match = re.search(r'PLAYBOOK-(\d+)', playbook_path.name)
        if match:
            pb_num = int(match.group(1))
            metadata_registry[pb_num] = metadata

    return metadata_registry
```

---

## 4. Template-Driven Updates

### Template System Architecture

```
Templates/
├── readme.template.md
├── index.template.md
├── ecosystem-map.template.md
├── system.template.mmd
└── guide.template.html

+ Metadata Registry (JSON)
  ↓
= Rendered Documentation
```

### README Template Example

```markdown
# {project_name}

> {tagline}

## Quick Start

{quick_start_content}

## Playbooks ({playbook_count} unique + {variant_count} variants)

{%- for pb in playbooks %}
### {pb.number}. [{pb.title}]({pb.file})
{pb.focus}
{%- if pb.variants %}
**Variants:** {pb.variants|join(", ")}
{%- endif %}
{% endfor %}

## Statistics

- **Total Playbooks:** {playbook_count} unique ({total_files} files)
- **Total Lines:** ~{total_lines:,}
- **Last Updated:** {last_updated}
```

### Index Template Example

```markdown
# Playbook Index

**Version:** {version}
**Last Updated:** {last_updated}
**Total Playbooks:** {playbook_count}

## Quick Reference Matrix

| # | Title | Focus | Difficulty | Prerequisites |
|---|-------|-------|------------|---------------|
{%- for pb in playbooks %}
| {pb.number} | [{pb.title}]({pb.file}) | {pb.focus} | {pb.difficulty} | {pb.prerequisites|default("None")} |
{%- endfor %}

## By Difficulty

### Beginner
{%- for pb in playbooks|selectattr("difficulty", "equalto", "Beginner") %}
- [{pb.title}]({pb.file})
{%- endfor %}

### Intermediate
{%- for pb in playbooks|selectattr("difficulty", "equalto", "Intermediate") %}
- [{pb.title}]({pb.file})
{%- endfor %}

### Advanced
{%- for pb in playbooks|selectattr("difficulty", "equalto", "Advanced") %}
- [{pb.title}]({pb.file})
{%- endfor %}
```

### Mermaid Template Example

```
%%{init: {'theme': 'base'}}%%

flowchart TB
{%- for layer in layers %}
    subgraph {layer.id}["{layer.icon} {layer.name} ({layer.count})"]
{%- for pb in layer.playbooks %}
        PB{pb.number}["<b>PB {pb.number}: {pb.title}</b><br/>{pb.focus}"]
{%- endfor %}
    end
{% endfor %}

    %% Dependencies
{%- for pb in playbooks %}
{%- for prereq in pb.prerequisites %}
    PB{prereq} --> PB{pb.number}
{%- endfor %}
{%- endfor %}

    %% Styling
{%- for layer in layers %}
    class {layer.playbook_ids|join(",")} {layer.style_class}
{%- endfor %}
```

### Template Rendering Engine

```python
from string import Template
import json

class DocTemplateEngine:
    """Simple template engine for documentation generation."""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        for template_file in self.template_dir.glob("*.template.*"):
            name = template_file.stem.replace(".template", "")
            self.templates[name] = template_file.read_text()

    def render(self, template_name: str, context: dict) -> str:
        """Render template with context."""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")

        # Simple variable substitution
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result

    def render_all(self, context: dict) -> dict[str, str]:
        """Render all templates with shared context."""
        return {
            name: self.render(name, context)
            for name in self.templates
        }
```

---

## 5. Cross-Reference Validation

### Link Validation Categories

```python
LINK_PATTERNS = {
    "markdown_link": r'\[([^\]]+)\]\(([^)]+)\)',
    "html_href": r'href=["\']([^"\']+)["\']',
    "mermaid_link": r'click\s+\w+\s+"([^"]+)"',
}

class LinkValidator:
    """Validate all cross-references in documentation."""

    def __init__(self, doc_root: Path):
        self.doc_root = doc_root
        self.issues = []

    def validate_file(self, file_path: Path) -> list[dict]:
        """Validate all links in a single file."""
        content = file_path.read_text()
        issues = []

        for link_type, pattern in LINK_PATTERNS.items():
            for match in re.finditer(pattern, content):
                link_target = match.group(2) if link_type == "markdown_link" else match.group(1)

                if not self._link_exists(link_target, file_path):
                    issues.append({
                        "file": str(file_path),
                        "link_type": link_type,
                        "target": link_target,
                        "line": content[:match.start()].count('\n') + 1,
                        "issue": "broken_link"
                    })

        return issues

    def _link_exists(self, target: str, source_file: Path) -> bool:
        """Check if link target exists."""
        # Skip external links
        if target.startswith(('http://', 'https://', 'mailto:')):
            return True

        # Skip anchors
        if target.startswith('#'):
            return True  # Could validate anchor exists

        # Resolve relative path
        if target.startswith('./'):
            target = target[2:]

        target_path = source_file.parent / target
        return target_path.exists()

    def validate_all(self) -> list[dict]:
        """Validate all documentation files."""
        issues = []
        for doc_file in self.doc_root.glob("**/*.md"):
            issues.extend(self.validate_file(doc_file))
        for doc_file in self.doc_root.glob("**/*.html"):
            issues.extend(self.validate_file(doc_file))
        return issues
```

### Orphan Detection

```python
def find_orphan_files(doc_root: Path, index_files: list[Path]) -> list[Path]:
    """Find files not referenced from any index."""

    # Collect all referenced files
    referenced = set()
    for index_file in index_files:
        content = index_file.read_text()
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+\.md)\)', content):
            referenced.add(match.group(2))

    # Find all actual files
    all_files = set(f.name for f in doc_root.glob("*.md"))

    # Orphans = files not referenced
    orphans = all_files - referenced - {f.name for f in index_files}

    return [doc_root / f for f in orphans]
```

### Duplicate Detection

```python
def find_duplicate_files(doc_root: Path) -> list[tuple[Path, Path]]:
    """Find files with highly similar content."""

    from difflib import SequenceMatcher

    files = list(doc_root.glob("*.md"))
    duplicates = []

    for i, file_a in enumerate(files):
        content_a = file_a.read_text()
        for file_b in files[i+1:]:
            content_b = file_b.read_text()

            similarity = SequenceMatcher(None, content_a, content_b).ratio()

            if similarity > 0.8:  # 80% similar
                duplicates.append((file_a, file_b, similarity))

    return duplicates
```

### Validation Report Generation

```python
def generate_validation_report(doc_root: Path) -> dict:
    """Generate comprehensive validation report."""

    validator = LinkValidator(doc_root)

    report = {
        "timestamp": datetime.now().isoformat(),
        "broken_links": validator.validate_all(),
        "orphan_files": [str(f) for f in find_orphan_files(doc_root)],
        "duplicate_files": [
            {"file_a": str(a), "file_b": str(b), "similarity": s}
            for a, b, s in find_duplicate_files(doc_root)
        ],
        "summary": {}
    }

    report["summary"] = {
        "broken_link_count": len(report["broken_links"]),
        "orphan_file_count": len(report["orphan_files"]),
        "duplicate_count": len(report["duplicate_files"]),
        "status": "PASS" if all(
            len(report[k]) == 0
            for k in ["broken_links", "orphan_files", "duplicate_files"]
        ) else "FAIL"
    }

    return report
```

---

## 6. Automated Synchronization Workflows

### Full Sync Workflow

```python
class DocumentationSynchronizer:
    """Orchestrate full documentation ecosystem synchronization."""

    def __init__(self, doc_root: Path):
        self.doc_root = doc_root
        self.metadata_registry = {}
        self.changes = []

    def sync(self) -> dict:
        """Execute full synchronization workflow."""

        # Phase 1: Extract metadata from all sources
        self.metadata_registry = extract_all_playbook_metadata(
            self.doc_root / "playbooks"
        )

        # Phase 2: Generate derived content
        context = self._build_template_context()

        # Phase 3: Update each file type
        updates = {
            "README.md": self._update_readme(context),
            "PLAYBOOK-INDEX.md": self._update_index(context),
            "ecosystem-map.md": self._update_ecosystem_map(context),
            "system.mmd": self._update_mermaid(context),
            "guide.html": self._update_html_guide(context),
        }

        # Phase 4: Validate
        validation = generate_validation_report(self.doc_root)

        # Phase 5: Write changes
        for filename, content in updates.items():
            if content:  # Only write if content changed
                (self.doc_root / filename).write_text(content)
                self.changes.append(filename)

        return {
            "updated_files": self.changes,
            "validation": validation,
            "metadata_count": len(self.metadata_registry)
        }

    def _build_template_context(self) -> dict:
        """Build context for template rendering."""
        playbooks = list(self.metadata_registry.values())

        return {
            "playbook_count": len(playbooks),
            "total_lines": sum(pb.get("line_count", 0) for pb in playbooks),
            "last_updated": datetime.now().strftime("%B %d, %Y"),
            "playbooks": playbooks,
            "layers": self._classify_layers(playbooks),
        }

    def _classify_layers(self, playbooks: list[dict]) -> list[dict]:
        """Classify playbooks into ecosystem layers."""

        LAYER_RULES = {
            "Meta": lambda pb: pb.get("number", 0) in [0, 7],
            "Foundation": lambda pb: pb.get("number", 0) in [1, 2, 3],
            "Advanced": lambda pb: pb.get("number", 0) in [4, 5, 6],
            "Operations": lambda pb: pb.get("number", 0) in [12, 15, 16, 19, 20],
            "Integration": lambda pb: pb.get("number", 0) in [8, 9, 10, 11],
            "Recursive": lambda pb: pb.get("number", 0) in [17, 18, 23, 24],
            "Orchestration": lambda pb: pb.get("number", 0) in [13, 14, 21, 22],
        }

        layers = []
        for layer_name, rule in LAYER_RULES.items():
            layer_pbs = [pb for pb in playbooks if rule(pb)]
            layers.append({
                "name": layer_name,
                "count": len(layer_pbs),
                "playbooks": layer_pbs
            })

        return layers
```

### Incremental Sync Workflow

```python
class IncrementalSynchronizer:
    """Only update files that have changed."""

    def __init__(self, doc_root: Path, cache_file: Path):
        self.doc_root = doc_root
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load previous sync state."""
        if self.cache_file.exists():
            return json.loads(self.cache_file.read_text())
        return {"file_hashes": {}, "last_sync": None}

    def _save_cache(self):
        """Save current sync state."""
        self.cache_file.write_text(json.dumps(self.cache, indent=2))

    def _file_hash(self, path: Path) -> str:
        """Compute hash of file content."""
        import hashlib
        return hashlib.md5(path.read_bytes()).hexdigest()

    def get_changed_files(self) -> list[Path]:
        """Identify files changed since last sync."""
        changed = []

        for pb_file in self.doc_root.glob("PLAYBOOK-*.md"):
            current_hash = self._file_hash(pb_file)
            cached_hash = self.cache["file_hashes"].get(str(pb_file))

            if current_hash != cached_hash:
                changed.append(pb_file)
                self.cache["file_hashes"][str(pb_file)] = current_hash

        return changed

    def sync_if_needed(self) -> dict:
        """Only sync if changes detected."""
        changed = self.get_changed_files()

        if not changed:
            return {"status": "no_changes", "updated_files": []}

        # Full sync triggered by changes
        synchronizer = DocumentationSynchronizer(self.doc_root)
        result = synchronizer.sync()

        # Update cache
        self.cache["last_sync"] = datetime.now().isoformat()
        self._save_cache()

        return result
```

---

## 7. Multi-File Update Orchestration

### Parallel Update Pattern

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelDocUpdater:
    """Update multiple documentation files in parallel."""

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def update_all(self, updates: dict[str, str]) -> dict:
        """Apply all updates in parallel."""

        loop = asyncio.get_event_loop()

        tasks = [
            loop.run_in_executor(
                self.executor,
                self._write_file,
                filename,
                content
            )
            for filename, content in updates.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            filename: "success" if not isinstance(result, Exception) else str(result)
            for filename, result in zip(updates.keys(), results)
        }

    def _write_file(self, filename: str, content: str) -> bool:
        """Write content to file with atomic semantics."""
        path = Path(filename)
        temp_path = path.with_suffix('.tmp')

        try:
            temp_path.write_text(content)
            temp_path.rename(path)  # Atomic on POSIX
            return True
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise
```

### Transactional Updates

```python
class TransactionalUpdater:
    """All-or-nothing updates with rollback capability."""

    def __init__(self, doc_root: Path):
        self.doc_root = doc_root
        self.backup_dir = doc_root / ".doc_backup"
        self.changes = []

    def begin(self):
        """Start transaction, backup current state."""
        self.backup_dir.mkdir(exist_ok=True)

        for doc_file in self.doc_root.glob("*.md"):
            backup_path = self.backup_dir / doc_file.name
            shutil.copy2(doc_file, backup_path)
            self.changes.append(doc_file.name)

    def update(self, filename: str, content: str):
        """Apply update within transaction."""
        (self.doc_root / filename).write_text(content)

    def commit(self):
        """Commit transaction, remove backups."""
        shutil.rmtree(self.backup_dir)
        self.changes = []

    def rollback(self):
        """Rollback transaction, restore backups."""
        for backup_file in self.backup_dir.glob("*"):
            dest = self.doc_root / backup_file.name
            shutil.copy2(backup_file, dest)

        shutil.rmtree(self.backup_dir)
        self.changes = []
```

### Ordered Dependency Updates

```python
def topological_sort_updates(updates: dict, dependencies: dict) -> list[str]:
    """Order updates by dependency graph."""

    # Build adjacency list
    graph = {f: [] for f in updates}
    in_degree = {f: 0 for f in updates}

    for file, deps in dependencies.items():
        for dep in deps:
            if dep in graph:
                graph[dep].append(file)
                in_degree[file] += 1

    # Kahn's algorithm
    queue = [f for f in updates if in_degree[f] == 0]
    order = []

    while queue:
        current = queue.pop(0)
        order.append(current)

        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return order

# Example usage:
DEPENDENCIES = {
    "PLAYBOOK-INDEX.md": ["README.md"],  # Index after README
    "ecosystem-map.md": ["PLAYBOOK-INDEX.md"],  # Map after Index
    "system.mmd": ["ecosystem-map.md"],  # Mermaid after Map
    "guide.html": ["system.mmd"],  # HTML after Mermaid
}

update_order = topological_sort_updates(updates, DEPENDENCIES)
for filename in update_order:
    apply_update(filename, updates[filename])
```

---

## 8. Integration Patterns

### Git Hook Integration

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run documentation sync check
python3 scripts/doc_sync_check.py

if [ $? -ne 0 ]; then
    echo "Documentation out of sync. Run 'make sync-docs' first."
    exit 1
fi
```

### CI/CD Pipeline Integration

```yaml
# .github/workflows/doc-sync.yml
name: Documentation Sync

on:
  push:
    paths:
      - 'playbooks/PLAYBOOK-*.md'
  pull_request:
    paths:
      - 'playbooks/PLAYBOOK-*.md'

jobs:
  sync-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check documentation sync
        run: |
          python3 scripts/doc_sync_check.py --strict

      - name: Auto-sync if needed
        if: failure()
        run: |
          python3 scripts/doc_sync.py
          git config user.name "Doc Bot"
          git config user.email "bot@example.com"
          git add .
          git commit -m "docs: auto-sync documentation"
          git push
```

### Makefile Integration

```makefile
# Makefile

.PHONY: sync-docs validate-docs watch-docs

sync-docs:
	python3 scripts/doc_sync.py

validate-docs:
	python3 scripts/doc_validate.py --report

watch-docs:
	watchexec -w playbooks/ -- make sync-docs

# Sync before commit
pre-commit: validate-docs sync-docs
	git add README.md PLAYBOOK-INDEX.md ecosystem-map.md
```

### Claude Code Integration

```markdown
## Claude Code Workflow

When updating playbook documentation:

1. **Edit playbook content**
   - Make changes to PLAYBOOK-*.md files

2. **Extract metadata**
   - Read updated playbook headers
   - Parse title, focus, prerequisites

3. **Update derived files in order**
   - README.md (entry point)
   - PLAYBOOK-INDEX.md (full reference)
   - ecosystem-map.md (visual)
   - system.mmd (flowchart)
   - guide.html (interactive)

4. **Validate cross-references**
   - Check all links resolve
   - Verify counts match
   - Confirm no orphans
```

---

## 9. Anti-Patterns to Avoid

### Anti-Pattern 1: Manual Count Updates

```markdown
❌ BAD: Manually updating counts
"We now have 25 playbooks" → manually edit in 6 files

✓ GOOD: Computed counts
playbook_count = len(glob("PLAYBOOK-*.md"))
# Automatically propagated to all derived files
```

### Anti-Pattern 2: Copy-Paste Synchronization

```markdown
❌ BAD: Copy-paste between files
1. Write description in README
2. Copy to INDEX
3. Copy to ecosystem-map
4. (Forget to copy to guide.html)

✓ GOOD: Single source of truth
1. Extract from playbook header (authoritative)
2. Template renders to all derived files
```

### Anti-Pattern 3: Ignoring Variants

```markdown
❌ BAD: Only tracking canonical files
- PLAYBOOK-7.md ✓
- PLAYBOOK-7-LOCAL-LLM-TUNING.md (ignored)

✓ GOOD: Explicit variant tracking
canonical: PLAYBOOK-7.md
variants:
  - PLAYBOOK-7-LOCAL-LLM-TUNING.md
  - PLAYBOOK-7-FRACTAL-REASONING.md
```

### Anti-Pattern 4: Hardcoded Paths

```markdown
❌ BAD: Hardcoded absolute paths
content = open("/home/user/project/playbooks/README.md")

✓ GOOD: Relative paths from root
DOC_ROOT = Path(__file__).parent
content = (DOC_ROOT / "playbooks" / "README.md").read_text()
```

### Anti-Pattern 5: Skipping Validation

```markdown
❌ BAD: Update without validation
1. Generate new content
2. Write to files
3. (Hope nothing broke)

✓ GOOD: Validate before write
1. Generate new content
2. Validate links
3. Check for orphans
4. Verify counts
5. Write to files
6. Re-validate
```

---

## 10. Templates and Checklists

### Documentation Update Checklist

```markdown
## Pre-Update
- [ ] Identify all changed playbooks
- [ ] Extract metadata from changed files
- [ ] Check for new/removed playbooks

## Update Phase
- [ ] Update README.md (counts, descriptions)
- [ ] Update PLAYBOOK-INDEX.md (full matrix)
- [ ] Update ecosystem-map.md (layer diagrams)
- [ ] Update system.mmd (flowchart nodes/edges)
- [ ] Update guide.html (cards, filters)

## Validation Phase
- [ ] All links resolve
- [ ] Counts match actual files
- [ ] No orphan files
- [ ] No duplicate content
- [ ] Mermaid renders correctly

## Post-Update
- [ ] Commit with descriptive message
- [ ] Verify CI passes
- [ ] Review rendered documentation
```

### Metadata Extraction Template

```json
{
  "playbook_id": "PB-N",
  "file": "PLAYBOOK-N-TITLE.md",
  "title": "Full Title",
  "focus": "One-line focus",
  "version": "1.0",
  "date": "Month Day, Year",
  "difficulty": "Beginner|Intermediate|Advanced",
  "time_estimate": "X-Y hours",
  "prerequisites": ["PB-X", "PB-Y"],
  "sections": ["Section 1", "Section 2"],
  "line_count": 500,
  "layer": "Foundation|Advanced|Operations|...",
  "variants": []
}
```

### Sync Configuration Template

```yaml
# doc-sync.yaml
documentation:
  root: ./playbooks

  sources:
    - pattern: "PLAYBOOK-*.md"
      type: playbook

  derived:
    - file: README.md
      template: readme.template.md

    - file: PLAYBOOK-INDEX.md
      template: index.template.md

    - file: ecosystem-map.md
      template: ecosystem-map.template.md

    - file: system.mmd
      template: system.template.mmd

    - file: guide.html
      template: guide.template.html

  validation:
    check_links: true
    check_orphans: true
    check_duplicates: true
    similarity_threshold: 0.8

  sync:
    mode: incremental  # or "full"
    cache_file: .doc-sync-cache.json
    backup: true
```

### Validation Report Template

```json
{
  "timestamp": "2025-12-12T10:30:00Z",
  "status": "PASS|FAIL",
  "summary": {
    "files_checked": 28,
    "links_checked": 150,
    "broken_links": 0,
    "orphan_files": 0,
    "duplicate_pairs": 0
  },
  "issues": [],
  "recommendations": []
}
```

---

## Quick Reference

### Key Formulas

```
Sync Time Savings = (Manual Time - Automated Time) / Manual Time
                  = (3.5 hours - 5 minutes) / 3.5 hours
                  = 97.6%

Drift Risk = Files × Update Frequency × Manual Error Rate
           = 6 files × weekly × 5%
           = 30% weekly drift risk without automation
```

### Command Reference

```bash
# Full sync
python3 scripts/doc_sync.py

# Validate only
python3 scripts/doc_sync.py --validate-only

# Incremental sync
python3 scripts/doc_sync.py --incremental

# Generate report
python3 scripts/doc_sync.py --report > sync_report.json

# Watch mode
python3 scripts/doc_sync.py --watch
```

### Integration Points

| System | Integration Method | Trigger |
|--------|-------------------|---------|
| Git | Pre-commit hook | Every commit |
| CI/CD | GitHub Action | Push/PR |
| Claude Code | Session workflow | Manual |
| IDE | File watcher | File save |

---

**Document Version:** 1.0
**Emergent From:** Documentation update session December 12, 2025
**Key Insight:** Template-driven automation reduces documentation drift by 97%+ while ensuring consistency across all derived files.
