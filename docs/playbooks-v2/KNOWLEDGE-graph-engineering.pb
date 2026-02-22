# Playbook 4: Knowledge Engineering with Claude
## Building Knowledge Graphs, Entity Extraction & Semantic Analysis

**Version:** 1.0
**Last Updated:** November 8, 2025
**Audience:** Data Engineers, Knowledge Graph Architects, AI Researchers
**Prerequisites:** Basic understanding of graph databases, ontologies, and semantic relationships

---

## Table of Contents

1. [Introduction](#introduction)
2. [Pattern Library](#pattern-library)
3. [Entity Extraction](#entity-extraction)
4. [Relationship Mapping](#relationship-mapping)
5. [Graph Construction](#graph-construction)
6. [Semantic Enrichment](#semantic-enrichment)
7. [Schema Design](#schema-design)
8. [Validation & Quality](#validation--quality)
9. [Production Patterns](#production-patterns)
10. [Cost Optimization](#cost-optimization)
11. [Troubleshooting](#troubleshooting)
12. [Real-World Use Cases](#real-world-use-cases)

---

## Introduction

### What is Knowledge Engineering with Claude?

Knowledge Engineering involves extracting, structuring, and enriching knowledge from unstructured data into machine-readable formats like knowledge graphs. Claude excels at:

- **Entity Recognition**: Identifying entities (people, places, concepts) in text
- **Relationship Extraction**: Discovering semantic relationships between entities
- **Ontology Design**: Creating taxonomies and classification systems
- **Graph Enrichment**: Adding metadata, properties, and contextual information
- **Schema Validation**: Ensuring data quality and consistency
- **Cross-Reference**: Linking entities across multiple documents

### Why Claude for Knowledge Engineering?

1. **Context Understanding**: 200K token context window for analyzing large documents
2. **Semantic Reasoning**: Natural language understanding for complex relationships
3. **Structured Output**: JSON/XML output for direct graph database integration
4. **Consistency**: Reliable entity recognition across diverse text sources
5. **Flexibility**: Adapts to custom ontologies and domain-specific taxonomies

### Playbook Goals

By the end of this playbook, you will:

- Extract entities and relationships from unstructured text
- Design custom ontologies for your knowledge domain
- Build production-ready knowledge graph pipelines
- Optimize costs for large-scale KG construction
- Validate and enrich existing knowledge graphs
- Integrate Claude with graph databases (Neo4j, SQLite, etc.)

---

## Pattern Library

### Official Examples Used in This Playbook

| Example | Category | Purpose | Location |
|---------|----------|---------|----------|
| Streaming Extended Thinking | Extended Thinking | Long-running entity extraction | Week 1-2 Examples |
| Tool Use with Extended Thinking | Extended Thinking | Graph database integration | Week 1-2 Examples |
| Prompt Caching - Large Context | Prompt Caching | Cache document corpus | Week 1-2 Examples |
| Prompt Caching - Tool Definitions | Prompt Caching | Cache entity schema | Week 1-2 Examples |
| Batch API - Multiple Documents | Batch Processing | Parallel entity extraction | Week 1-2 Examples |

### Pattern Combinations for Knowledge Engineering

```
Pattern: Document Analysis → Entity Extraction
- Extended Thinking for complex entity recognition
- Prompt Caching for document corpus
- Streaming for real-time entity display

Pattern: Relationship Mapping → Graph Construction
- Tool Use for database writes
- Batch Processing for bulk relationship extraction
- Extended Thinking for ambiguous relationships

Pattern: Schema Validation → Quality Assurance
- Prompt Caching for ontology/schema
- Extended Thinking for consistency checks
- Tool Use for automated corrections
```

---

## Entity Extraction

### Basic Entity Recognition

**Goal**: Extract named entities from unstructured text

```python
import anthropic

client = anthropic.Anthropic()

def extract_entities(text: str, entity_types: list = None):
    """
    Extract entities from text with optional type filtering.

    Args:
        text: Source text for entity extraction
        entity_types: Optional list of entity types to extract
                     (e.g., ['person', 'organization', 'concept'])

    Returns:
        List of entities with type, name, and context
    """
    if entity_types is None:
        entity_types = ['person', 'organization', 'location', 'concept',
                       'technology', 'event', 'date']

    prompt = f"""Extract entities from the following text. For each entity, provide:
- type: Entity type from {entity_types}
- name: The entity name as it appears in text
- canonical_name: Standardized version of the name
- context: Brief context where the entity appears

Return as JSON array of entities.

Text:
{text}
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    # Extract JSON from response
    content = response.content[0].text
    # Parse JSON (handle markdown code blocks)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]

    entities = json.loads(content.strip())
    return entities


# Example usage
text = """
Claude Code is an interactive CLI tool developed by Anthropic for software engineering.
It uses the Claude Sonnet 4.5 model and supports features like extended thinking,
prompt caching, and tool use. The tool is particularly effective for knowledge graph
construction, as demonstrated in the NLKE methodology by Eyal.
"""

entities = extract_entities(text)
for entity in entities:
    print(f"{entity['type']}: {entity['name']} → {entity['canonical_name']}")
```

**Expected Output**:
```
technology: Claude Code → claude_code_cli
organization: Anthropic → anthropic
technology: Claude Sonnet 4.5 → claude_sonnet_4_5
concept: extended thinking → extended_thinking
concept: prompt caching → prompt_caching
concept: knowledge graph → knowledge_graph
concept: NLKE methodology → nlke_methodology
person: Eyal → eyal
```

### Advanced Entity Extraction with Extended Thinking

**Goal**: Use extended thinking for complex, ambiguous entity recognition

```python
def extract_entities_with_thinking(text: str, domain: str = "general"):
    """
    Extract entities using extended thinking for complex domains.

    Args:
        text: Source text
        domain: Knowledge domain (e.g., 'medical', 'legal', 'technical')

    Returns:
        Entities with reasoning about classification decisions
    """
    system_prompt = f"""You are a knowledge engineering assistant specialized in {domain} domain.
Extract entities while reasoning about:
1. Entity type disambiguation (is "Python" a language or animal?)
2. Entity boundaries (where does a compound entity start/end?)
3. Canonical naming (standardize variations like "AI" vs "Artificial Intelligence")
4. Co-reference resolution (link "Claude" and "it" to same entity)

Provide your reasoning, then output entities as JSON.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        thinking={
            "type": "enabled",
            "budget_tokens": 3000
        },
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Extract entities from this {domain} text:\n\n{text}"
        }]
    )

    # Extract thinking and answer
    thinking_content = ""
    answer_content = ""

    for block in response.content:
        if block.type == "thinking":
            thinking_content = block.thinking
        elif block.type == "text":
            answer_content = block.text

    import json
    if "```json" in answer_content:
        answer_content = answer_content.split("```json")[1].split("```")[0]

    entities = json.loads(answer_content.strip())

    return {
        "entities": entities,
        "reasoning": thinking_content,
        "confidence": response.usage.output_tokens / response.usage.input_tokens
    }
```

---

## Relationship Mapping

### Basic Relationship Extraction

**Goal**: Discover semantic relationships between entities

```python
def extract_relationships(text: str, entities: list = None):
    """
    Extract relationships between entities in text.

    Args:
        text: Source text
        entities: Optional pre-extracted entities

    Returns:
        List of relationships with type, source, target, and properties
    """
    entity_context = ""
    if entities:
        entity_names = [e['name'] for e in entities]
        entity_context = f"Focus on relationships involving: {', '.join(entity_names)}\n\n"

    prompt = f"""Extract semantic relationships from this text. For each relationship:
- source: Source entity
- relation_type: Relationship type (e.g., 'created_by', 'part_of', 'uses', 'enables')
- target: Target entity
- properties: Additional properties (strength, temporal context, etc.)

{entity_context}Text:
{text}

Return as JSON array of relationships.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    content = response.content[0].text
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]

    relationships = json.loads(content.strip())
    return relationships


# Example usage
text = """
Claude Code was developed by Anthropic to assist with software engineering tasks.
It leverages the Claude Sonnet 4.5 model, which supports extended thinking for
complex reasoning. Extended thinking enables the model to reason before responding,
improving quality for tasks like knowledge graph construction.
"""

relationships = extract_relationships(text)
for rel in relationships:
    print(f"{rel['source']} --[{rel['relation_type']}]--> {rel['target']}")
```

**Expected Output**:
```
Claude Code --[developed_by]--> Anthropic
Claude Code --[assists_with]--> software engineering
Claude Code --[leverages]--> Claude Sonnet 4.5
Claude Sonnet 4.5 --[supports]--> extended thinking
extended thinking --[enables]--> reasoning
extended thinking --[improves_quality_for]--> knowledge graph construction
```

### Relationship Type Taxonomy

Common relationship types for knowledge graphs:

**Structural Relationships**:
- `part_of` - Component relationships
- `contains` - Container relationships
- `member_of` - Membership in groups/categories

**Causal Relationships**:
- `causes` - Causal relationships
- `enables` - Capability enablement
- `requires` - Dependency relationships

**Semantic Relationships**:
- `similar_to` - Similarity relationships
- `opposite_of` - Antonym relationships
- `example_of` - Instance-of relationships

**Temporal Relationships**:
- `precedes` - Temporal ordering
- `follows` - Sequential relationships
- `concurrent_with` - Simultaneous relationships

**Creation/Attribution**:
- `created_by` - Authorship
- `developed_by` - Development attribution
- `maintained_by` - Maintenance responsibility

---

## Graph Construction

### SQLite Knowledge Graph Implementation

**Goal**: Build a complete KG construction pipeline with SQLite

```python
import sqlite3
import json
from typing import List, Dict, Any
from datetime import datetime

class KnowledgeGraphBuilder:
    """Production knowledge graph construction with SQLite."""

    def __init__(self, db_path: str, anthropic_api_key: str):
        self.db_path = db_path
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self._init_database()

    def _init_database(self):
        """Initialize KG database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Nodes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                canonical_name TEXT,
                description TEXT,
                properties TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Edges table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                properties TEXT,  -- JSON
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES nodes(id),
                FOREIGN KEY (target_id) REFERENCES nodes(id)
            )
        ''')

        # Create indices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation_type)')

        conn.commit()
        conn.close()

    def extract_and_store_entities(self, text: str, source_doc: str = None):
        """Extract entities from text and store in graph."""
        # Extract entities with Claude
        entities = self._extract_entities_claude(text)

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stored_ids = []
        for entity in entities:
            node_id = self._generate_node_id(entity)

            # Check if node exists
            cursor.execute('SELECT id FROM nodes WHERE id = ?', (node_id,))
            exists = cursor.fetchone()

            if not exists:
                # Insert new node
                cursor.execute('''
                    INSERT INTO nodes (id, type, name, canonical_name, description, properties)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    node_id,
                    entity.get('type'),
                    entity.get('name'),
                    entity.get('canonical_name'),
                    entity.get('context', ''),
                    json.dumps({
                        'source_document': source_doc,
                        'original_context': entity.get('context')
                    })
                ))
                stored_ids.append(node_id)

        conn.commit()
        conn.close()

        return stored_ids

    def extract_and_store_relationships(self, text: str, entities: List[Dict] = None):
        """Extract relationships and store as edges."""
        # Extract relationships with Claude
        relationships = self._extract_relationships_claude(text, entities)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stored_count = 0
        for rel in relationships:
            source_id = self._generate_node_id({'canonical_name': rel['source']})
            target_id = self._generate_node_id({'canonical_name': rel['target']})

            # Check if both nodes exist
            cursor.execute('SELECT id FROM nodes WHERE id IN (?, ?)', (source_id, target_id))
            results = cursor.fetchall()

            if len(results) == 2:
                # Both nodes exist, create edge
                cursor.execute('''
                    INSERT INTO edges (source_id, target_id, relation_type, properties, confidence)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    source_id,
                    target_id,
                    rel['relation_type'],
                    json.dumps(rel.get('properties', {})),
                    rel.get('confidence', 1.0)
                ))
                stored_count += 1

        conn.commit()
        conn.close()

        return stored_count

    def _extract_entities_claude(self, text: str) -> List[Dict]:
        """Extract entities using Claude."""
        prompt = f"""Extract entities from this text. Return JSON array with:
- type: entity type
- name: entity name
- canonical_name: standardized name (lowercase, underscores)
- context: where it appears

Text: {text}"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]

        return json.loads(content.strip())

    def _extract_relationships_claude(self, text: str, entities: List[Dict] = None) -> List[Dict]:
        """Extract relationships using Claude."""
        entity_context = ""
        if entities:
            entity_names = [e['canonical_name'] for e in entities]
            entity_context = f"Known entities: {', '.join(entity_names)}\n\n"

        prompt = f"""{entity_context}Extract relationships from this text. Return JSON array with:
- source: source entity canonical name
- target: target entity canonical name
- relation_type: relationship type (lowercase, underscores)
- confidence: 0.0-1.0

Text: {text}"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]

        return json.loads(content.strip())

    def _generate_node_id(self, entity: Dict) -> str:
        """Generate deterministic node ID from canonical name."""
        canonical = entity.get('canonical_name', entity.get('name', '')).lower()
        canonical = canonical.replace(' ', '_').replace('-', '_')
        return canonical

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count nodes by type
        cursor.execute('SELECT type, COUNT(*) FROM nodes GROUP BY type')
        nodes_by_type = dict(cursor.fetchall())

        # Count total edges
        cursor.execute('SELECT COUNT(*) FROM edges')
        total_edges = cursor.fetchone()[0]

        # Count edges by relation type
        cursor.execute('SELECT relation_type, COUNT(*) FROM edges GROUP BY relation_type')
        edges_by_type = dict(cursor.fetchall())

        conn.close()

        return {
            'total_nodes': sum(nodes_by_type.values()),
            'total_edges': total_edges,
            'nodes_by_type': nodes_by_type,
            'edges_by_type': edges_by_type
        }


# Usage Example
kg = KnowledgeGraphBuilder(
    db_path="knowledge_graph.db",
    anthropic_api_key="your-api-key"
)

# Process a document
document = """
Claude Code is an interactive CLI tool developed by Anthropic. It uses the
Claude Sonnet 4.5 model which supports extended thinking. Extended thinking
enables complex reasoning for tasks like knowledge graph construction.
"""

# Extract and store entities
entity_ids = kg.extract_and_store_entities(document, source_doc="claude_code_intro.txt")
print(f"Stored {len(entity_ids)} entities")

# Extract and store relationships
rel_count = kg.extract_and_store_relationships(document)
print(f"Stored {rel_count} relationships")

# Get statistics
stats = kg.get_stats()
print(f"Graph stats: {stats}")
```

---

## Semantic Enrichment

### Adding Metadata to Entities

**Goal**: Enrich entities with additional semantic information

```python
def enrich_entity(entity_id: str, entity_name: str, knowledge_graph_db: str):
    """
    Enrich an entity with additional metadata using Claude.

    Returns:
        Dictionary with enriched metadata
    """
    prompt = f"""Provide semantic enrichment for this entity: "{entity_name}"

Return JSON with:
- aliases: List of alternative names/spellings
- category_hierarchy: Taxonomic classification (general to specific)
- properties: Domain-specific properties (key-value pairs)
- related_concepts: Conceptually related entities
- description: 2-sentence description
- tags: List of relevant tags/keywords

Be concise and factual.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    content = response.content[0].text
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]

    enrichment = json.loads(content.strip())

    # Store enrichment in database
    conn = sqlite3.connect(knowledge_graph_db)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE nodes
        SET properties = json_patch(COALESCE(properties, '{}'), ?),
            description = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        json.dumps({
            'enrichment': enrichment,
            'enriched_at': datetime.now().isoformat()
        }),
        enrichment.get('description', ''),
        entity_id
    ))

    conn.commit()
    conn.close()

    return enrichment
```

### Batch Enrichment with Prompt Caching

**Goal**: Enrich multiple entities efficiently using cached ontology

```python
def batch_enrich_entities(entity_ids: List[str], ontology: Dict, kg_db: str):
    """
    Enrich multiple entities using cached ontology for consistency.

    Args:
        entity_ids: List of entity IDs to enrich
        ontology: Domain ontology/taxonomy (will be cached)
        kg_db: Path to knowledge graph database
    """
    # Prepare ontology as cached system prompt
    ontology_text = json.dumps(ontology, indent=2)

    conn = sqlite3.connect(kg_db)
    cursor = conn.cursor()

    # Get entities
    placeholders = ','.join('?' * len(entity_ids))
    cursor.execute(f'''
        SELECT id, name, type FROM nodes WHERE id IN ({placeholders})
    ''', entity_ids)

    entities = [{'id': row[0], 'name': row[1], 'type': row[2]} for row in cursor.fetchall()]

    # Process in batches of 10
    batch_size = 10
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i+batch_size]

        entity_list = "\n".join([f"- {e['id']}: {e['name']} ({e['type']})" for e in batch])

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8192,
            system=[{
                "type": "text",
                "text": f"Domain Ontology:\n{ontology_text}",
                "cache_control": {"type": "ephemeral"}
            }],
            messages=[{
                "role": "user",
                "content": f"""Enrich these entities based on the ontology. Return JSON array:

Entities:
{entity_list}

For each entity provide: aliases, category_hierarchy, properties, description.
"""
            }]
        )

        content = response.content[0].text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]

        enrichments = json.loads(content.strip())

        # Store enrichments
        for entity, enrichment in zip(batch, enrichments):
            cursor.execute('''
                UPDATE nodes
                SET properties = json_set(
                    COALESCE(properties, '{}'),
                    '$.enrichment',
                    ?
                ),
                description = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                json.dumps(enrichment),
                enrichment.get('description', ''),
                entity['id']
            ))

        conn.commit()

    conn.close()
```

---

## Schema Design

### Ontology Design with Claude

**Goal**: Design custom ontology for domain-specific knowledge

```python
def design_ontology(domain: str, sample_texts: List[str], requirements: str = ""):
    """
    Design a custom ontology for a knowledge domain.

    Args:
        domain: Knowledge domain (e.g., 'medical', 'software engineering')
        sample_texts: Representative texts from the domain
        requirements: Specific ontology requirements

    Returns:
        Ontology specification with entity types, relationships, and rules
    """
    samples_text = "\n\n---\n\n".join(sample_texts[:3])  # Use first 3 samples

    prompt = f"""Design an ontology for the {domain} domain.

Requirements:
{requirements}

Sample texts from domain:
{samples_text}

Provide JSON ontology with:
1. entity_types: List of entity types with descriptions and examples
2. relationship_types: List of relationship types with semantics
3. constraints: Rules for valid relationships
4. hierarchy: Taxonomic organization of entity types
5. properties: Common properties for each entity type

The ontology should be:
- Comprehensive but not overly complex
- Consistent with domain terminology
- Extensible for future additions
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 4000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract answer
    answer_content = ""
    for block in response.content:
        if block.type == "text":
            answer_content = block.text

    import json
    if "```json" in answer_content:
        answer_content = answer_content.split("```json")[1].split("```")[0]

    ontology = json.loads(answer_content.strip())

    return ontology


# Example: Design ontology for API documentation domain
sample_docs = [
    "The Messages API supports prompt caching for large contexts...",
    "Extended thinking enables Claude to reason before responding...",
    "Tool use allows Claude to interact with external systems..."
]

ontology = design_ontology(
    domain="API Documentation",
    sample_texts=sample_docs,
    requirements="Focus on API features, capabilities, and usage patterns"
)

print(json.dumps(ontology, indent=2))
```

---

## Validation & Quality

### Consistency Validation

**Goal**: Validate knowledge graph consistency and identify errors

```python
def validate_graph_consistency(kg_db: str, ontology: Dict):
    """
    Validate knowledge graph against ontology constraints.

    Returns:
        Validation report with errors and warnings
    """
    conn = sqlite3.connect(kg_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    report = {
        "errors": [],
        "warnings": [],
        "stats": {}
    }

    # Validate entity types
    cursor.execute('SELECT DISTINCT type FROM nodes')
    node_types = [row[0] for row in cursor.fetchall()]

    valid_types = [et['name'] for et in ontology.get('entity_types', [])]
    for node_type in node_types:
        if node_type not in valid_types:
            report["warnings"].append({
                "type": "invalid_entity_type",
                "message": f"Entity type '{node_type}' not in ontology",
                "severity": "medium"
            })

    # Validate relationship types
    cursor.execute('SELECT DISTINCT relation_type FROM edges')
    rel_types = [row[0] for row in cursor.fetchall()]

    valid_rels = [rt['name'] for rt in ontology.get('relationship_types', [])]
    for rel_type in rel_types:
        if rel_type not in valid_rels:
            report["warnings"].append({
                "type": "invalid_relationship_type",
                "message": f"Relationship type '{rel_type}' not in ontology",
                "severity": "medium"
            })

    # Validate relationship constraints
    constraints = ontology.get('constraints', [])
    for constraint in constraints:
        if constraint['type'] == 'valid_source_target':
            # Check if source/target types are valid for relationship
            relation = constraint['relation']
            valid_sources = constraint['valid_sources']
            valid_targets = constraint['valid_targets']

            cursor.execute('''
                SELECT e.id, e.relation_type, s.type as source_type, t.type as target_type
                FROM edges e
                JOIN nodes s ON e.source_id = s.id
                JOIN nodes t ON e.target_id = t.id
                WHERE e.relation_type = ?
            ''', (relation,))

            for row in cursor.fetchall():
                if row['source_type'] not in valid_sources:
                    report["errors"].append({
                        "type": "constraint_violation",
                        "message": f"Edge {row['id']}: Invalid source type {row['source_type']} for {relation}",
                        "severity": "high"
                    })

                if row['target_type'] not in valid_targets:
                    report["errors"].append({
                        "type": "constraint_violation",
                        "message": f"Edge {row['id']}: Invalid target type {row['target_type']} for {relation}",
                        "severity": "high"
                    })

    # Statistics
    cursor.execute('SELECT COUNT(*) FROM nodes')
    report["stats"]["total_nodes"] = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM edges')
    report["stats"]["total_edges"] = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COUNT(*) FROM nodes n
        WHERE NOT EXISTS (SELECT 1 FROM edges WHERE source_id = n.id OR target_id = n.id)
    ''')
    report["stats"]["isolated_nodes"] = cursor.fetchone()[0]

    conn.close()

    return report
```

---

## Production Patterns

### Complete Pipeline: Document → Knowledge Graph

```python
class ProductionKGPipeline:
    """
    Production-ready knowledge graph construction pipeline.
    Combines: Caching + Thinking + Batch Processing + Tool Use
    """

    def __init__(self, kg_db: str, anthropic_api_key: str, ontology: Dict):
        self.kg_db = kg_db
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.ontology = ontology
        self.ontology_text = json.dumps(ontology, indent=2)

        # Initialize graph builder
        self.builder = KnowledgeGraphBuilder(kg_db, anthropic_api_key)

    def process_document(self, document_text: str, document_id: str):
        """
        Process single document: extract entities and relationships.
        Uses extended thinking + caching for consistency.
        """
        # Step 1: Extract entities with cached ontology
        entities = self._extract_entities_cached(document_text)

        # Step 2: Store entities
        entity_ids = []
        for entity in entities:
            node_id = self.builder._generate_node_id(entity)
            self._store_node(node_id, entity, document_id)
            entity_ids.append(node_id)

        # Step 3: Extract relationships
        relationships = self._extract_relationships_cached(document_text, entities)

        # Step 4: Store relationships
        rel_count = 0
        for rel in relationships:
            if self._store_edge(rel):
                rel_count += 1

        return {
            "document_id": document_id,
            "entities_extracted": len(entities),
            "relationships_extracted": rel_count,
            "entity_ids": entity_ids
        }

    def process_corpus_batch(self, documents: List[Dict[str, str]]):
        """
        Process multiple documents in batch with 50% cost savings.

        Args:
            documents: List of {"id": str, "text": str}
        """
        # Create batch requests for entity extraction
        batch_requests = []
        for doc in documents:
            batch_requests.append({
                "custom_id": f"entities-{doc['id']}",
                "params": {
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 4096,
                    "system": [{
                        "type": "text",
                        "text": f"Domain Ontology:\n{self.ontology_text}",
                        "cache_control": {"type": "ephemeral"}
                    }],
                    "messages": [{
                        "role": "user",
                        "content": f"Extract entities from this document according to the ontology:\n\n{doc['text']}"
                    }]
                }
            })

        # Submit batch
        message_batch = self.client.messages.batches.create(requests=batch_requests)

        # Poll for completion
        import time
        while True:
            batch_status = self.client.messages.batches.retrieve(message_batch.id)
            if batch_status.processing_status == "ended":
                break
            time.sleep(10)

        # Retrieve and process results
        results = []
        for result in self.client.messages.batches.results(message_batch.id):
            if result.result.type == "succeeded":
                doc_id = result.custom_id.replace("entities-", "")
                content = result.result.message.content[0].text

                # Parse entities
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                entities = json.loads(content.strip())

                # Store entities
                for entity in entities:
                    node_id = self.builder._generate_node_id(entity)
                    self._store_node(node_id, entity, doc_id)

                results.append({
                    "document_id": doc_id,
                    "entities_count": len(entities)
                })

        return results

    def _extract_entities_cached(self, text: str) -> List[Dict]:
        """Extract entities using cached ontology."""
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=[{
                "type": "text",
                "text": f"Domain Ontology:\n{self.ontology_text}",
                "cache_control": {"type": "ephemeral"}
            }],
            thinking={
                "type": "enabled",
                "budget_tokens": 2000
            },
            messages=[{
                "role": "user",
                "content": f"Extract entities from this text according to the ontology:\n\n{text}"
            }]
        )

        # Extract answer
        answer_content = ""
        for block in response.content:
            if block.type == "text":
                answer_content = block.text

        if "```json" in answer_content:
            answer_content = answer_content.split("```json")[1].split("```")[0]

        return json.loads(answer_content.strip())

    def _extract_relationships_cached(self, text: str, entities: List[Dict]) -> List[Dict]:
        """Extract relationships using cached ontology."""
        entity_names = [e['canonical_name'] for e in entities]
        entity_context = f"Known entities: {', '.join(entity_names)}"

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=[{
                "type": "text",
                "text": f"Domain Ontology:\n{self.ontology_text}\n\n{entity_context}",
                "cache_control": {"type": "ephemeral"}
            }],
            messages=[{
                "role": "user",
                "content": f"Extract relationships from this text:\n\n{text}"
            }]
        )

        content = response.content[0].text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]

        return json.loads(content.strip())

    def _store_node(self, node_id: str, entity: Dict, source_doc: str):
        """Store node in database."""
        conn = sqlite3.connect(self.kg_db)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM nodes WHERE id = ?', (node_id,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO nodes (id, type, name, canonical_name, description, properties)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                node_id,
                entity.get('type'),
                entity.get('name'),
                entity.get('canonical_name'),
                entity.get('description', ''),
                json.dumps({'source_document': source_doc})
            ))

        conn.commit()
        conn.close()

    def _store_edge(self, relationship: Dict) -> bool:
        """Store edge in database."""
        conn = sqlite3.connect(self.kg_db)
        cursor = conn.cursor()

        source_id = relationship.get('source')
        target_id = relationship.get('target')

        # Verify both nodes exist
        cursor.execute('SELECT COUNT(*) FROM nodes WHERE id IN (?, ?)', (source_id, target_id))
        if cursor.fetchone()[0] != 2:
            conn.close()
            return False

        cursor.execute('''
            INSERT INTO edges (source_id, target_id, relation_type, properties, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            source_id,
            target_id,
            relationship.get('relation_type'),
            json.dumps(relationship.get('properties', {})),
            relationship.get('confidence', 1.0)
        ))

        conn.commit()
        conn.close()

        return True
```

---

## Cost Optimization

### Cost Breakdown for Knowledge Engineering

**Typical Costs** (Claude Sonnet 4.5):

| Task | Input Tokens | Output Tokens | Cost per Document |
|------|--------------|---------------|-------------------|
| Entity Extraction | 1,000 | 500 | $0.0105 |
| Relationship Extraction | 1,000 | 300 | $0.0075 |
| Semantic Enrichment | 500 | 200 | $0.0045 |
| **Total per Document** | | | **$0.0225** |

### Optimization Strategies

**1. Prompt Caching for Ontology (85-90% savings)**
```python
# Cache the ontology for all extractions
system=[{
    "type": "text",
    "text": ontology_text,  # Reused across all requests
    "cache_control": {"type": "ephemeral"}
}]

# Cost reduction:
# - First request: $0.0225 (cache creation)
# - Subsequent requests: ~$0.0025 (90% savings)
```

**2. Batch Processing (50% savings)**
```python
# Process 100 documents in batch
batch_requests = [create_request(doc) for doc in documents]
batch = client.messages.batches.create(requests=batch_requests)

# Cost reduction:
# - Standard API: $2.25 for 100 docs
# - Batch API: $1.13 for 100 docs (50% savings)
```

**3. Combined: Caching + Batch (92-95% savings)**
```python
# Batch requests with cached ontology
batch_requests = []
for doc in documents:
    batch_requests.append({
        "custom_id": doc['id'],
        "params": {
            "model": "claude-sonnet-4-5-20250929",
            "system": [{
                "type": "text",
                "text": ontology_text,
                "cache_control": {"type": "ephemeral"}
            }],
            "messages": [{"role": "user", "content": doc['text']}]
        }
    })

# Cost reduction:
# - Standard: $2.25 for 100 docs
# - Optimized: ~$0.15 for 100 docs (93% savings!)
```

### Real-World Cost Example

**Scenario**: Process 1,000 technical documents for knowledge graph construction

| Strategy | Cost | Time | Notes |
|----------|------|------|-------|
| Standard API (no optimization) | $22.50 | ~30 min | Individual requests |
| Prompt Caching only | $2.50 | ~30 min | 85-90% savings |
| Batch Processing only | $11.25 | 24 hours | 50% savings |
| **Caching + Batch** | **$1.50** | **24 hours** | **93% savings** |

---

## Troubleshooting

### Common Issues and Solutions

**Issue: Inconsistent Entity Names**
- **Problem**: Same entity extracted with different names ("AI" vs "Artificial Intelligence")
- **Solution**: Use canonical naming in prompts, implement post-processing normalization
```python
# Add to prompt:
"Always provide canonical_name: standardized lowercase version with underscores"
```

**Issue: Missing Relationships**
- **Problem**: Claude doesn't extract implicit relationships
- **Solution**: Use extended thinking + explicit relationship guidance
```python
thinking={"type": "enabled", "budget_tokens": 3000}
# Prompt: "Consider both explicit and implicit relationships..."
```

**Issue: Hallucinated Entities**
- **Problem**: Claude extracts entities not present in text
- **Solution**: Add grounding constraint + verification step
```python
# Prompt: "Only extract entities explicitly mentioned in the text.
# Provide evidence: quote the exact text where each entity appears."
```

**Issue: Schema Drift**
- **Problem**: Entities/relationships don't match ontology over time
- **Solution**: Use cached ontology + periodic validation
```python
# Cache ontology in system prompt
# Run validation_report() weekly to detect drift
```

**Issue: Low Relationship Confidence**
- **Problem**: Uncertain about extracted relationships
- **Solution**: Use extended thinking to assess confidence
```python
thinking={"type": "enabled", "budget_tokens": 2000}
# Output includes confidence scores 0.0-1.0
# Filter relationships with confidence < 0.7
```

---

## Real-World Use Cases

### Use Case 1: API Documentation Knowledge Graph

**Goal**: Build searchable knowledge graph from API docs

```python
# 1. Design ontology
ontology = design_ontology(
    domain="API Documentation",
    sample_texts=[...],  # Sample API docs
    requirements="Track endpoints, parameters, authentication, examples"
)

# 2. Process documentation
pipeline = ProductionKGPipeline("api_docs_kg.db", api_key, ontology)

docs = [
    {"id": "messages_api", "text": messages_api_docs},
    {"id": "batch_api", "text": batch_api_docs},
    # ... more docs
]

results = pipeline.process_corpus_batch(docs)

# 3. Query the graph
conn = sqlite3.connect("api_docs_kg.db")
cursor = conn.cursor()

# Find all endpoints that support caching
cursor.execute('''
    SELECT DISTINCT n.name
    FROM nodes n
    JOIN edges e ON n.id = e.source_id
    WHERE n.type = 'api_endpoint'
    AND e.relation_type = 'supports'
    AND e.target_id = 'prompt_caching'
''')

caching_endpoints = [row[0] for row in cursor.fetchall()]
```

### Use Case 2: Research Paper Network Analysis

**Goal**: Extract citation network and concept relationships from papers

```python
# Extract entities: papers, authors, concepts, methods
entities = extract_entities_with_thinking(
    paper_text,
    domain="machine_learning_research"
)

# Extract relationships: cites, proposes, improves_upon, uses
relationships = extract_relationships(paper_text, entities)

# Build citation network
for rel in relationships:
    if rel['relation_type'] == 'cites':
        add_citation_edge(rel['source'], rel['target'])
```

### Use Case 3: Codebase Understanding

**Goal**: Map software architecture and component relationships

```python
# Extract entities: classes, functions, modules, patterns
code_entities = extract_entities(
    codebase_summary,
    entity_types=['class', 'function', 'module', 'pattern', 'technology']
)

# Extract relationships: inherits, calls, uses, implements
code_relationships = extract_relationships(codebase_summary)

# Identify architectural patterns
cursor.execute('''
    SELECT s.name as component, GROUP_CONCAT(t.name) as dependencies
    FROM edges e
    JOIN nodes s ON e.source_id = s.id
    JOIN nodes t ON e.target_id = t.id
    WHERE e.relation_type = 'depends_on'
    GROUP BY s.name
''')
```

---

## Summary

### Key Takeaways

1. **Entity Extraction**: Use extended thinking for complex domain-specific entities
2. **Relationship Mapping**: Define clear relationship taxonomies in ontology
3. **Cost Optimization**: Combine caching + batch for 92-95% cost savings
4. **Validation**: Implement schema validation to ensure graph quality
5. **Production Patterns**: Use cached ontology + batch processing for scale

### Cost-Optimized Workflow

```
Design Ontology → Cache in System Prompt → Batch Process Documents →
Validate Results → Enrich Entities → Deploy Graph
```

**Expected Costs** (1,000 documents):
- Without optimization: $22.50
- With optimization: $1.50 (93% savings)

### Next Steps

1. Define your domain ontology using the design_ontology() pattern
2. Set up SQLite knowledge graph with KnowledgeGraphBuilder
3. Process documents using ProductionKGPipeline with caching + batch
4. Validate graph consistency with validation reports
5. Enrich entities and deploy for querying

---

## Additional Resources

**Related Playbooks**:
- Playbook 1: Cost Optimization (prompt caching, batch processing)
- Playbook 2: Extended Thinking (complex reasoning for entity disambiguation)
- Playbook 3: Agent Development (building KG construction agents)

**Tools**:
- SQLite for graph storage
- Neo4j for advanced graph queries
- Knowledge Graph visualization tools

**Official Examples**:
- All Week 1-2 examples in `/claude-cookbook-kg/`
- Batch API examples for parallel processing
- Prompt caching examples for ontology caching

---

**Playbook Version**: 1.0
**Last Updated**: November 8, 2025
**Maintained By**: NLKE Project
**Feedback**: Submit issues or suggestions to project repository

