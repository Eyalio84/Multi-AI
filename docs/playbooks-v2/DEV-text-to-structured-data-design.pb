# PLAYBOOK-10: Text to Structured Data - Design Document

**Status**: 🟡 Design Phase
**Purpose**: Convert unstructured text into structured data (JSON, schemas, tables, graphs)
**Date**: November 30, 2025

---

## Overview

PLAYBOOK-10 teaches systematic approaches for converting unstructured text (documentation, logs, API specs, natural language) into structured formats (JSON schemas, database models, configuration files, knowledge graphs).

### Core Use Cases

1. **API Documentation → OpenAPI Schemas**
2. **Logs → Structured Events (JSON)**
3. **Natural Language → Database Models**
4. **Documentation → Knowledge Graphs**
5. **Config Files → Validated Schemas**
6. **Conversations → Structured Session Data**

---

## Templates (4-5 templates)

### Template 1: Schema Extraction Template

**File**: `/templates/workflows/schema_extraction_template.json`

```json
{
  "template_id": "schema_extract_001",
  "title": "Text to Schema Extraction Pattern",
  "category": "workflow",
  "complexity": "intermediate",
  "description": "Extract structured schemas from unstructured text",

  "extraction_phases": {
    "1_analysis": {
      "description": "Understand the text structure and identify entities",
      "actions": [
        "Read full text",
        "Identify entities/objects",
        "Find relationships",
        "Detect patterns"
      ],
      "thinking_budget": "2000-3000",
      "output": "List of entities + relationships"
    },

    "2_schema_design": {
      "description": "Design schema structure",
      "actions": [
        "Define types for each entity",
        "Specify properties and constraints",
        "Determine required vs optional fields",
        "Add validation rules"
      ],
      "thinking_budget": "3000-5000",
      "output": "Schema draft (JSON Schema or similar)"
    },

    "3_validation": {
      "description": "Validate schema against original text",
      "actions": [
        "Check all entities captured",
        "Verify relationships preserved",
        "Test with examples",
        "Refine based on gaps"
      ],
      "thinking_budget": "1000-2000",
      "output": "Validated schema"
    },

    "4_documentation": {
      "description": "Document schema with examples",
      "actions": [
        "Add descriptions to all fields",
        "Include example instances",
        "Document constraints",
        "Provide usage notes"
      ],
      "thinking_budget": "1000-1500",
      "output": "Complete documented schema"
    }
  },

  "schema_formats": {
    "json_schema": {
      "when": "API contracts, data validation",
      "benefits": "Standard, widely supported, validator-ready"
    },
    "typescript_interfaces": {
      "when": "Frontend/backend contracts",
      "benefits": "Type-safe, IDE support"
    },
    "pydantic_models": {
      "when": "Python data validation",
      "benefits": "Runtime validation, serialization"
    },
    "graphql_schema": {
      "when": "API design, graph structures",
      "benefits": "Self-documenting, type system"
    }
  },

  "extraction_patterns": {
    "entity_extraction": {
      "description": "Identify nouns/objects as entities",
      "keywords": ["User", "Order", "Product", "Session"],
      "example": "User has many Orders → User entity + Order entity + relationship"
    },

    "property_extraction": {
      "description": "Identify attributes from descriptions",
      "keywords": ["has", "contains", "includes", "with"],
      "example": "User has email and password → User.email, User.password"
    },

    "constraint_extraction": {
      "description": "Identify validation rules",
      "keywords": ["required", "optional", "must", "should", "between", "max", "min"],
      "example": "Email is required → email: { type: 'string', required: true }"
    },

    "relationship_extraction": {
      "description": "Identify connections between entities",
      "keywords": ["has many", "belongs to", "references", "links to"],
      "example": "User has many Orders → User 1:N Order relationship"
    }
  },

  "anti_patterns": [
    "Skipping validation phase (schema may miss edge cases)",
    "Over-engineering schema (too many optional fields)",
    "Under-specifying constraints (validation too loose)",
    "Missing documentation (schema unclear to users)"
  ],

  "examples": [
    {
      "input": "A user account has an email (required), password (required), and optional profile picture URL",
      "output_json_schema": {
        "type": "object",
        "properties": {
          "email": { "type": "string", "format": "email" },
          "password": { "type": "string", "minLength": 8 },
          "profilePictureUrl": { "type": "string", "format": "uri" }
        },
        "required": ["email", "password"]
      }
    }
  ]
}
```

### Template 2: Log Parsing to Structured Events

**File**: `/templates/workflows/log_parsing_template.json`

```json
{
  "template_id": "log_parse_001",
  "title": "Log Parsing to Structured Events",
  "category": "workflow",
  "complexity": "intermediate",

  "parsing_workflow": {
    "1_sample_analysis": {
      "description": "Analyze log samples to identify structure",
      "actions": [
        "Collect representative log lines",
        "Identify common patterns",
        "Find delimiters and structure",
        "Detect timestamps, levels, messages"
      ],
      "thinking_budget": "2000-3000"
    },

    "2_pattern_definition": {
      "description": "Define parsing patterns (regex or structured)",
      "actions": [
        "Create regex for each log format",
        "Define field extraction rules",
        "Handle multi-line logs",
        "Account for variations"
      ],
      "thinking_budget": "3000-4000"
    },

    "3_schema_creation": {
      "description": "Design event schema",
      "actions": [
        "Define event types",
        "Specify fields per type",
        "Add metadata fields",
        "Include context fields"
      ],
      "thinking_budget": "2000-3000"
    },

    "4_transformation": {
      "description": "Transform logs to structured JSON events",
      "actions": [
        "Apply parsing patterns",
        "Validate extracted data",
        "Enrich with metadata",
        "Handle parsing errors"
      ],
      "thinking_budget": "1000-2000"
    }
  },

  "log_patterns": {
    "timestamp": {
      "pattern": "\\d{4}-\\d{2}-\\d{2}[T ]\\d{2}:\\d{2}:\\d{2}",
      "field": "timestamp",
      "type": "datetime"
    },
    "log_level": {
      "pattern": "(DEBUG|INFO|WARN|ERROR|FATAL)",
      "field": "level",
      "type": "enum"
    },
    "message": {
      "pattern": ".*",
      "field": "message",
      "type": "string"
    }
  },

  "structured_output": {
    "format": "JSON Lines (JSONL)",
    "schema": {
      "timestamp": "ISO 8601 datetime",
      "level": "log_level enum",
      "message": "string",
      "metadata": "object (optional)",
      "context": "object (optional)"
    }
  },

  "anti_patterns": [
    "Assuming single log format (logs often vary)",
    "Losing original message (always preserve raw log)",
    "Ignoring multi-line logs (stack traces, etc.)",
    "Not handling parsing failures (logs can be malformed)"
  ]
}
```

### Template 3: Natural Language to Data Model

**File**: `/templates/workflows/nl_to_data_model_template.json`

```json
{
  "template_id": "nl_datamodel_001",
  "title": "Natural Language to Data Model Pattern",
  "category": "workflow",
  "complexity": "advanced",

  "conversion_process": {
    "1_requirements_extraction": {
      "description": "Extract data requirements from natural language",
      "techniques": [
        "Entity recognition (nouns → tables/models)",
        "Action recognition (verbs → operations)",
        "Attribute recognition (adjectives → properties)",
        "Relationship recognition (prepositions → associations)"
      ],
      "thinking_budget": "4000-6000",
      "example": "'Users can create posts with tags' → User entity, Post entity, Tag entity, User->Post (1:N), Post->Tag (M:N)"
    },

    "2_normalization": {
      "description": "Normalize data model (reduce redundancy)",
      "actions": [
        "Identify duplicate data",
        "Extract to separate entities",
        "Define foreign keys",
        "Apply normalization forms"
      ],
      "thinking_budget": "3000-4000"
    },

    "3_schema_generation": {
      "description": "Generate database schema or ORM models",
      "outputs": [
        "SQL CREATE TABLE statements",
        "ORM class definitions (SQLAlchemy, TypeORM)",
        "NoSQL schema (if applicable)",
        "GraphQL type definitions"
      ],
      "thinking_budget": "2000-3000"
    },

    "4_validation": {
      "description": "Validate model against requirements",
      "checks": [
        "All entities captured",
        "Relationships correct",
        "Constraints represented",
        "Operations supported"
      ],
      "thinking_budget": "1500-2500"
    }
  },

  "linguistic_patterns": {
    "entity_indicators": ["User", "Account", "Product", "Order", "Item"],
    "relationship_phrases": [
      "has many",
      "belongs to",
      "contains",
      "includes",
      "references",
      "associated with"
    ],
    "constraint_phrases": [
      "must have",
      "required",
      "optional",
      "unique",
      "between",
      "at least",
      "at most"
    ]
  },

  "example": {
    "input_text": "A library system where books can be borrowed by members. Each book has a title, author, and ISBN. Members have a name and email. A member can borrow multiple books, and we need to track the borrow date and return date.",

    "extracted_entities": {
      "Book": ["title", "author", "isbn"],
      "Member": ["name", "email"],
      "Borrow": ["book_id", "member_id", "borrow_date", "return_date"]
    },

    "relationships": [
      "Book 1:N Borrow",
      "Member 1:N Borrow"
    ],

    "output_sql": "CREATE TABLE books (\n  id SERIAL PRIMARY KEY,\n  title VARCHAR(255) NOT NULL,\n  author VARCHAR(255) NOT NULL,\n  isbn VARCHAR(13) UNIQUE NOT NULL\n);\n\nCREATE TABLE members (\n  id SERIAL PRIMARY KEY,\n  name VARCHAR(255) NOT NULL,\n  email VARCHAR(255) UNIQUE NOT NULL\n);\n\nCREATE TABLE borrows (\n  id SERIAL PRIMARY KEY,\n  book_id INT REFERENCES books(id),\n  member_id INT REFERENCES members(id),\n  borrow_date DATE NOT NULL,\n  return_date DATE\n);"
  }
}
```

### Template 4: API Documentation to OpenAPI

**File**: `/templates/workflows/docs_to_openapi_template.json`

```json
{
  "template_id": "docs_openapi_001",
  "title": "Documentation to OpenAPI Schema",
  "category": "workflow",
  "complexity": "advanced",

  "extraction_workflow": {
    "1_endpoint_discovery": {
      "description": "Identify all API endpoints from docs",
      "look_for": [
        "HTTP methods (GET, POST, PUT, DELETE)",
        "URL paths (/users, /users/:id)",
        "Route parameters",
        "Query parameters"
      ],
      "thinking_budget": "3000-4000"
    },

    "2_request_schema": {
      "description": "Extract request body schemas",
      "actions": [
        "Identify request examples",
        "Extract field types",
        "Determine required fields",
        "Document validation rules"
      ],
      "thinking_budget": "4000-5000"
    },

    "3_response_schema": {
      "description": "Extract response schemas",
      "actions": [
        "Identify response examples",
        "Extract response codes (200, 400, 404, etc.)",
        "Define response bodies",
        "Document error formats"
      ],
      "thinking_budget": "4000-5000"
    },

    "4_openapi_generation": {
      "description": "Generate OpenAPI 3.1 specification",
      "structure": {
        "openapi": "3.1.0",
        "info": "API metadata",
        "servers": "Base URLs",
        "paths": "All endpoints with operations",
        "components": "Reusable schemas"
      },
      "thinking_budget": "3000-4000"
    }
  },

  "openapi_structure": {
    "info": {
      "title": "Extracted from docs",
      "version": "Inferred or specified",
      "description": "From docs introduction"
    },
    "paths": {
      "/{resource}": {
        "get|post|put|delete": {
          "summary": "From docs",
          "parameters": "Extracted",
          "requestBody": "Schema extracted",
          "responses": "All status codes + schemas"
        }
      }
    },
    "components": {
      "schemas": "Reusable data models"
    }
  },

  "extraction_hints": {
    "http_methods": "Look for GET, POST, PUT, DELETE, PATCH",
    "path_parameters": "Look for :id, {id}, <id> patterns",
    "query_parameters": "Look for ?param=value descriptions",
    "headers": "Look for Authorization, Content-Type mentions",
    "status_codes": "200 success, 400 bad request, 404 not found, 500 error"
  }
}
```

### Template 5: Conversation to Session Data

**File**: `/templates/workflows/conversation_to_session_template.json`

```json
{
  "template_id": "conv_session_001",
  "title": "Conversation to Structured Session Data",
  "category": "workflow",
  "complexity": "intermediate",

  "session_extraction": {
    "1_turn_segmentation": {
      "description": "Break conversation into turns",
      "identify": [
        "User messages",
        "Assistant messages",
        "Tool invocations",
        "Tool results"
      ],
      "thinking_budget": "1500-2500"
    },

    "2_intent_extraction": {
      "description": "Extract user intent per turn",
      "categories": [
        "question",
        "request",
        "clarification",
        "feedback",
        "approval"
      ],
      "thinking_budget": "2000-3000"
    },

    "3_action_extraction": {
      "description": "Extract actions taken by assistant",
      "categories": [
        "information_provided",
        "tool_used",
        "file_modified",
        "plan_created",
        "question_asked"
      ],
      "thinking_budget": "2000-3000"
    },

    "4_state_extraction": {
      "description": "Extract session state changes",
      "track": [
        "Files created/modified",
        "Decisions made",
        "Plans created",
        "Issues identified",
        "Tasks completed"
      ],
      "thinking_budget": "2500-3500"
    }
  },

  "structured_output_schema": {
    "session_id": "string",
    "start_time": "datetime",
    "end_time": "datetime",
    "turns": [
      {
        "turn_number": "integer",
        "speaker": "user|assistant|system",
        "message": "string",
        "intent": "enum",
        "actions": ["array of actions"],
        "tool_calls": ["array of tool invocations"],
        "state_changes": ["array of state modifications"]
      }
    ],
    "summary": {
      "topic": "string",
      "outcome": "string",
      "files_modified": ["array"],
      "decisions_made": ["array"]
    }
  }
}
```

---

## Tools (4-5 tools)

### Tool 1: Schema Extractor

**File**: `/synthesis-rules/tools/schema_extractor.py`

```python
"""
Schema Extractor

Extracts JSON schemas from unstructured text:
- Entity recognition (nouns → object types)
- Property extraction (attributes from descriptions)
- Constraint detection (validation rules)
- Relationship mapping (connections between entities)
- Generates JSON Schema, TypeScript interfaces, or Pydantic models
"""
```

### Tool 2: Log Parser Generator

**File**: `/synthesis-rules/tools/log_parser_generator.py`

```python
"""
Log Parser Generator

Generates parsing logic for logs:
- Analyzes log samples to detect patterns
- Creates regex patterns for extraction
- Generates parsing code (Python/JS)
- Defines structured event schema
- Validates parser against test logs
"""
```

### Tool 3: Natural Language to SQL

**File**: `/synthesis-rules/tools/nl_to_sql.py`

```python
"""
Natural Language to SQL Schema

Converts natural language data requirements to SQL:
- Extracts entities from text
- Identifies relationships
- Determines constraints (NOT NULL, UNIQUE, etc.)
- Generates CREATE TABLE statements
- Produces ERD diagrams (optional)
"""
```

### Tool 4: OpenAPI Generator

**File**: `/synthesis-rules/tools/openapi_generator.py`

```python
"""
OpenAPI Generator

Converts API docs to OpenAPI 3.1 specs:
- Extracts endpoints and HTTP methods
- Parses request/response examples
- Infers schemas from examples
- Generates complete OpenAPI YAML/JSON
- Validates against OpenAPI spec
"""
```

### Tool 5: Session Structurizer

**File**: `/synthesis-rules/tools/session_structurizer.py`

```python
"""
Session Structurizer

Converts conversation logs to structured session data:
- Segments conversation into turns
- Extracts intent per message
- Tracks actions and tool uses
- Records state changes
- Generates session summary JSON
"""
```

---

## Integration with Synthesis Rules Engine

### Rule Validation

```python
from engine import RuleEngine

engine = RuleEngine()
engine.load_rules()

# Validate a text-to-schema workflow
result = engine.validate_combination(
    features=["schema_extraction", "extended_thinking", "prompt_caching"],
    context={
        "input_type": "api_documentation",
        "output_format": "openapi_3.1",
        "complexity": "advanced"
    }
)

# Returns applicable templates and suggested thinking budget
```

### Template Discovery

```python
from synthesis_rules.query import TemplateQuery

tq = TemplateQuery()

# Find text-to-structured-data templates
templates = tq.find_by_playbook("PLAYBOOK-10")

# Find tools for schema extraction
tools = tq.find_tools("schema_extraction")
```

---

## Meta-Pattern Detection for PLAYBOOK-10

While extracting rules, we'll detect patterns for PLAYBOOK-10:
- Schema inference patterns
- Entity recognition techniques
- Constraint extraction methods
- Relationship mapping strategies
- Validation approaches

**Source**: Templates, PLAYBOOK-4 (Knowledge Engineering), existing tool usage

---

## Summary

**PLAYBOOK-10: Text to Structured Data** provides:

### 5 Templates
1. Schema Extraction (general-purpose)
2. Log Parsing (logs → structured events)
3. Natural Language to Data Model (requirements → DB schema)
4. API Docs to OpenAPI (docs → OpenAPI spec)
5. Conversation to Session Data (chat logs → structured sessions)

### 5 Tools
1. Schema Extractor (entity + property extraction)
2. Log Parser Generator (regex + parsing logic)
3. Natural Language to SQL (text → SQL DDL)
4. OpenAPI Generator (docs → OpenAPI)
5. Session Structurizer (conversations → JSON)

### Integration
- All connect to synthesis-rules engine
- Use extended thinking for complex extractions (4000-8000 tokens)
- Support prompt caching for repeated schema extraction
- Template-driven approach (reusable patterns)

### Use Cases
- API contract generation from docs
- Database schema design from requirements
- Log aggregation and analysis
- Knowledge graph construction
- Session management and replay

---

**Status**: 🟢 Design Complete - Ready for Implementation
**Next**: Extract meta-patterns from existing sources, then implement templates/tools in Phase 3
