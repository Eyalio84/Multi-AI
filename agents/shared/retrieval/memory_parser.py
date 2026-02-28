#!/usr/bin/env python3
"""
Memory Parser — Markdown to Indexable Chunks

Reads markdown files from the NLKE memory directory, splits them
at ## and ### headings, and produces MemoryChunk objects compatible
with BM25Index/EmbeddingManager duck-typing contract.

Level 0 dependency — no imports from retrieval package.

Created: February 8, 2026
"""

import os
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Any, Optional


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class MemoryChunk:
    """Single indexable section from a memory markdown file.

    Duck-type compatible with BM25Index/EmbeddingManager:
    - node_id: str (required by both)
    - name: str (required by both)
    - description: str (required by both)
    - intent_keywords: str (required by BM25Index for boost check)
    - node_type: str (for consistency with KGNode pattern)
    """
    node_id: str
    name: str
    description: str
    node_type: str = "memory_chunk"
    intent_keywords: str = ""
    # Memory-specific metadata
    source_file: str = ""
    directory: str = ""
    heading_level: int = 0
    line_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryResult:
    """Query result from MemoryFusion with score breakdown."""
    chunk: MemoryChunk
    bm25_score: float = 0.0
    vector_score: float = 0.0
    final_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.chunk.node_id,
            "name": self.chunk.name,
            "source_file": self.chunk.source_file,
            "directory": self.chunk.directory,
            "heading_level": self.chunk.heading_level,
            "description": self.chunk.description[:200],
            "bm25_score": round(self.bm25_score, 4),
            "vector_score": round(self.vector_score, 4),
            "final_score": round(self.final_score, 4),
        }


# ============================================================================
# Heading regex — matches ## and ### but NOT # or ####
# ============================================================================

HEADING_RE = re.compile(r'^(#{2,3})\s+(.+)$')


# ============================================================================
# Parser
# ============================================================================

def parse_markdown_sections(filepath: str, memory_root: str) -> List[MemoryChunk]:
    """Parse a markdown file into per-heading MemoryChunks.

    Splits at ## and ### headings. #### and deeper are treated as
    inline content (not split points). Handles fenced code blocks
    to avoid false splits on heading-like lines inside ```.

    Args:
        filepath: Absolute path to the .md file
        memory_root: Absolute path to memory root directory

    Returns:
        List of MemoryChunk objects, one per heading section + preamble
    """
    try:
        with open(filepath, "r", errors="replace") as f:
            lines = f.readlines()
    except (OSError, IOError):
        return []

    # Compute relative path and directory
    rel_path = os.path.relpath(filepath, memory_root)
    parts = rel_path.split(os.sep)
    directory = parts[0] if len(parts) > 1 else ""

    chunks: List[MemoryChunk] = []
    current_name = ""
    current_level = 0
    current_body: List[str] = []
    current_line = 1
    inside_code_block = False
    preamble_title = os.path.basename(filepath)

    def _flush_section():
        """Save current section as a MemoryChunk."""
        nonlocal current_name, current_body, current_level, current_line
        body = "\n".join(current_body).strip()
        if not current_name and not body:
            return
        name = current_name or preamble_title
        level = current_level or 1
        prefix = "#" * level
        node_id = f"{rel_path}::{prefix} {name}"
        chunks.append(MemoryChunk(
            node_id=node_id,
            name=name,
            description=body,
            source_file=rel_path,
            directory=directory,
            heading_level=level,
            line_number=current_line,
        ))

    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")

        # Track fenced code blocks
        if line.strip().startswith("```"):
            inside_code_block = not inside_code_block
            current_body.append(line)
            continue

        if inside_code_block:
            current_body.append(line)
            continue

        # Check for ## or ### heading
        m = HEADING_RE.match(line)
        if m:
            hashes = m.group(1)
            heading_text = m.group(2).strip()
            level = len(hashes)

            # Check for # title in preamble (before any ##)
            # Already handled below

            # Flush previous section
            _flush_section()

            # Start new section
            current_name = heading_text
            current_level = level
            current_body = []
            current_line = i
            continue

        # Check for h1 title (# Title) — use as preamble name, not a split point
        if line.startswith("# ") and not line.startswith("##") and not chunks and not current_name:
            preamble_title = line[2:].strip()
            current_body.append(line)
            continue

        current_body.append(line)

    # Flush last section
    _flush_section()

    return chunks


def scan_memory_directory(memory_root: str) -> Tuple[List[MemoryChunk], Dict[str, float]]:
    """Recursively scan memory directory for .md files and parse all.

    Uses os.listdir (not find) for Termux/PRoot compatibility.

    Args:
        memory_root: Absolute path to memory root directory

    Returns:
        Tuple of (all_chunks, {absolute_filepath: mtime})
    """
    all_chunks: List[MemoryChunk] = []
    mtimes: Dict[str, float] = {}

    def _walk(dirpath: str):
        try:
            entries = sorted(os.listdir(dirpath))
        except OSError:
            return
        for entry in entries:
            full = os.path.join(dirpath, entry)
            if os.path.isdir(full):
                _walk(full)
            elif entry.endswith(".md"):
                chunks = parse_markdown_sections(full, memory_root)
                all_chunks.extend(chunks)
                try:
                    mtimes[full] = os.path.getmtime(full)
                except OSError:
                    mtimes[full] = 0.0

    _walk(memory_root)
    return all_chunks, mtimes


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    print("memory_parser.py — Memory Parser self-test")
    print("=" * 60)

    MEMORY_ROOT = "/storage/self/primary/Download/44nlke/NLKE/memory"

    # Test scan
    chunks, mtimes = scan_memory_directory(MEMORY_ROOT)
    print(f"\nScanned: {len(mtimes)} files, {len(chunks)} chunks")

    # Per-file breakdown
    files_seen: Dict[str, int] = {}
    for c in chunks:
        files_seen[c.source_file] = files_seen.get(c.source_file, 0) + 1

    print(f"\nPer-file breakdown:")
    for f, count in sorted(files_seen.items()):
        print(f"  {count:3d} chunks | {f}")

    # Sample chunks
    print(f"\nSample chunks (first 5):")
    for c in chunks[:5]:
        desc_preview = c.description[:80].replace("\n", " ")
        print(f"  [{c.heading_level}] {c.node_id}")
        print(f"      name: {c.name}")
        print(f"      desc: {desc_preview}...")
        print()

    # Verify no chunks from inside code blocks
    code_block_test = [c for c in chunks if "```" in c.name]
    if code_block_test:
        print(f"WARNING: {len(code_block_test)} chunks have ``` in name (code block leak)")
    else:
        print("Code block handling: OK (no false splits)")

    # Verify chunk counts
    assert len(chunks) >= 50, f"Expected 50+ chunks, got {len(chunks)}"
    assert len(mtimes) >= 5, f"Expected 5+ files, got {len(mtimes)}"

    print(f"\n{'=' * 60}")
    print("memory_parser.py OK")
