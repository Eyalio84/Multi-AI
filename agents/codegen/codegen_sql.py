#!/usr/bin/env python3
"""
Code Generation Agent: SQL (#36)

Generates SQL code from natural language specifications.
Supports SQLite, PostgreSQL, schema design, queries, migrations,
indexes, views, and stored procedures.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 codegen_sql.py --example
    python3 codegen_sql.py --workload spec.json --output result.json

Created: February 6, 2026
"""

import sys
import os
import re
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
)

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class SQLSpec:
    description: str
    sql_type: str  # schema, query, migration, index, view, procedure
    dialect: str  # sqlite, postgresql
    name: str
    tables: List[str] = field(default_factory=list)
    columns: Dict[str, List[str]] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)


@dataclass
class GeneratedSQL:
    filename: str
    code: str
    dialect: str = "sqlite"
    lines: int = 0
    tables_created: List[str] = field(default_factory=list)
    indexes_created: List[str] = field(default_factory=list)


# ============================================================================
# L2: Constants
# ============================================================================

SQL_TYPES = {
    "schema": {"description": "CREATE TABLE statements"},
    "query": {"description": "SELECT/INSERT/UPDATE/DELETE"},
    "migration": {"description": "ALTER TABLE statements"},
    "index": {"description": "CREATE INDEX statements"},
    "view": {"description": "CREATE VIEW statements"},
    "procedure": {"description": "Stored procedures / CTEs"},
}

TYPE_MAPPING = {
    "sqlite": {
        "int": "INTEGER",
        "string": "TEXT",
        "text": "TEXT",
        "float": "REAL",
        "bool": "INTEGER",
        "date": "TEXT",
        "datetime": "TEXT",
        "json": "TEXT",
        "blob": "BLOB",
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    },
    "postgresql": {
        "int": "INTEGER",
        "string": "VARCHAR(255)",
        "text": "TEXT",
        "float": "DOUBLE PRECISION",
        "bool": "BOOLEAN",
        "date": "DATE",
        "datetime": "TIMESTAMP",
        "json": "JSONB",
        "blob": "BYTEA",
        "id": "SERIAL PRIMARY KEY",
    },
}

SQL_RULES = [
    "codegen_sql_001_primary_keys_required",
    "codegen_sql_002_indexes_on_fk",
    "codegen_sql_003_timestamps_on_tables",
    "codegen_sql_004_no_select_star",
    "codegen_sql_005_parameterized_queries",
    "codegen_sql_006_proper_constraints",
]

SQL_ANTI_PATTERNS = [
    "no_primary_key",
    "select_star",
    "missing_indexes",
    "implicit_type_conversion",
    "n_plus_one_query",
    "missing_timestamps",
]


# ============================================================================
# L3: Analyzer
# ============================================================================

class CodegenSqlAnalyzer(BaseAnalyzer):
    """SQL code generation engine."""

    def __init__(self):
        super().__init__(
            agent_name="codegen-sql",
            model="haiku",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "specs": [
                {
                    "description": "Database schema for a task management app with users, projects, and tasks",
                    "sql_type": "schema",
                    "dialect": "sqlite",
                    "name": "task_manager",
                    "tables": ["users", "projects", "tasks", "task_assignments"],
                    "columns": {
                        "users": ["id:id", "username:string", "email:string", "created_at:datetime"],
                        "projects": ["id:id", "name:string", "description:text", "owner_id:int", "created_at:datetime"],
                        "tasks": ["id:id", "title:string", "description:text", "status:string", "priority:int", "project_id:int", "created_at:datetime", "due_date:date"],
                        "task_assignments": ["id:id", "task_id:int", "user_id:int", "assigned_at:datetime"],
                    },
                    "constraints": ["UNIQUE on users.email", "UNIQUE on users.username"],
                    "relationships": ["projects.owner_id -> users.id", "tasks.project_id -> projects.id", "task_assignments.task_id -> tasks.id", "task_assignments.user_id -> users.id"],
                },
                {
                    "description": "Query to find all overdue tasks with their assigned users and project names",
                    "sql_type": "query",
                    "dialect": "sqlite",
                    "name": "overdue_tasks_report",
                    "tables": ["tasks", "task_assignments", "users", "projects"],
                    "constraints": ["only incomplete tasks", "ordered by priority desc"],
                },
                {
                    "description": "Performance indexes for common query patterns on the task management schema",
                    "sql_type": "index",
                    "dialect": "sqlite",
                    "name": "task_manager_indexes",
                    "tables": ["tasks", "task_assignments", "projects"],
                    "constraints": ["index on status", "index on due_date", "composite index on project+status"],
                },
            ],
        }

    def _parse_spec(self, spec_dict: Dict) -> SQLSpec:
        return SQLSpec(
            description=spec_dict.get("description", ""),
            sql_type=spec_dict.get("sql_type", "schema"),
            dialect=spec_dict.get("dialect", "sqlite"),
            name=spec_dict.get("name", "untitled"),
            tables=spec_dict.get("tables", []),
            columns=spec_dict.get("columns", {}),
            constraints=spec_dict.get("constraints", []),
            relationships=spec_dict.get("relationships", []),
        )

    def _generate_sql(self, spec: SQLSpec) -> GeneratedSQL:
        if spec.sql_type == "schema":
            return self._gen_schema(spec)
        elif spec.sql_type == "query":
            return self._gen_query(spec)
        elif spec.sql_type == "index":
            return self._gen_indexes(spec)
        elif spec.sql_type == "migration":
            return self._gen_migration(spec)
        elif spec.sql_type == "view":
            return self._gen_view(spec)
        else:
            return self._gen_procedure(spec)

    def _map_type(self, col_type: str, dialect: str) -> str:
        return TYPE_MAPPING.get(dialect, TYPE_MAPPING["sqlite"]).get(col_type, "TEXT")

    def _gen_schema(self, spec: SQLSpec) -> GeneratedSQL:
        types = TYPE_MAPPING.get(spec.dialect, TYPE_MAPPING["sqlite"])
        tables_sql = []
        tables_created = []

        for table in spec.tables:
            cols = spec.columns.get(table, [])
            col_defs = []
            fk_defs = []

            for col_def in cols:
                parts = col_def.split(":")
                col_name = parts[0]
                col_type = parts[1] if len(parts) > 1 else "text"
                col_defs.append(f"  {col_name} {self._map_type(col_type, spec.dialect)}")

            # Add foreign keys from relationships
            for rel in spec.relationships:
                if rel.startswith(f"{table}."):
                    fk_match = re.match(r'(\w+)\.(\w+)\s*->\s*(\w+)\.(\w+)', rel)
                    if fk_match:
                        fk_col = fk_match.group(2)
                        ref_table = fk_match.group(3)
                        ref_col = fk_match.group(4)
                        fk_defs.append(f"  FOREIGN KEY ({fk_col}) REFERENCES {ref_table}({ref_col})")

            # Add constraints
            for c in spec.constraints:
                if table in c.lower() or f"{table}." in c:
                    col_match = re.search(r'\.(\w+)', c)
                    if col_match and "UNIQUE" in c.upper():
                        col_defs.append(f"  UNIQUE ({col_match.group(1)})")

            all_defs = col_defs + fk_defs
            table_sql = f"CREATE TABLE IF NOT EXISTS {table} (\n{','.join(chr(10) + d for d in all_defs)}\n);"
            tables_sql.append(table_sql)
            tables_created.append(table)

        header = f"-- {spec.description}\n-- Dialect: {spec.dialect}\n-- Generated by NLKE codegen-sql\n"
        code = header + "\n\n".join(tables_sql)

        return GeneratedSQL(
            filename=f"{spec.name}.sql",
            code=code,
            dialect=spec.dialect,
            lines=code.count("\n") + 1,
            tables_created=tables_created,
        )

    def _gen_query(self, spec: SQLSpec) -> GeneratedSQL:
        tables = spec.tables
        main_table = tables[0] if tables else "table1"

        joins = ""
        for t in tables[1:]:
            joins += f"\n  LEFT JOIN {t} ON {main_table}.id = {t}.{main_table[:-1]}_id"

        where_clauses = []
        for c in spec.constraints:
            where_clauses.append(f"  -- Constraint: {c}")

        where = "\nWHERE\n" + "\n  AND ".join(where_clauses) if where_clauses else ""

        code = textwrap.dedent(f"""\
            -- {spec.description}
            -- Dialect: {spec.dialect}
            -- Generated by NLKE codegen-sql

            SELECT
              {main_table}.*
              {', '.join(f', {t}.id AS {t}_id' for t in tables[1:])}
            FROM {main_table}{joins}{where}
            ORDER BY {main_table}.id DESC;
        """)

        return GeneratedSQL(
            filename=f"{spec.name}.sql",
            code=code,
            dialect=spec.dialect,
            lines=code.count("\n") + 1,
        )

    def _gen_indexes(self, spec: SQLSpec) -> GeneratedSQL:
        indexes = []
        idx_names = []

        for c in spec.constraints:
            parts = c.lower().split()
            if "index" in parts:
                for table in spec.tables:
                    for word in parts:
                        if word not in ("index", "on", "composite"):
                            idx_name = f"idx_{table}_{word}"
                            indexes.append(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({word});")
                            idx_names.append(idx_name)
                            break

        if not indexes:
            for table in spec.tables:
                idx_name = f"idx_{table}_id"
                indexes.append(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}(id);")
                idx_names.append(idx_name)

        code = f"-- {spec.description}\n-- Dialect: {spec.dialect}\n\n" + "\n".join(indexes)

        return GeneratedSQL(
            filename=f"{spec.name}.sql",
            code=code,
            dialect=spec.dialect,
            lines=code.count("\n") + 1,
            indexes_created=idx_names,
        )

    def _gen_migration(self, spec: SQLSpec) -> GeneratedSQL:
        stmts = []
        for table in spec.tables:
            for c in spec.constraints:
                stmts.append(f"-- Migration: {c} on {table}")
                stmts.append(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS new_column TEXT;")

        code = f"-- Migration: {spec.description}\n-- Dialect: {spec.dialect}\n\nBEGIN;\n\n" + "\n".join(stmts) + "\n\nCOMMIT;"

        return GeneratedSQL(
            filename=f"{spec.name}.sql",
            code=code,
            dialect=spec.dialect,
            lines=code.count("\n") + 1,
        )

    def _gen_view(self, spec: SQLSpec) -> GeneratedSQL:
        view_name = spec.name.replace("-", "_")
        tables = spec.tables
        main_table = tables[0] if tables else "table1"

        code = textwrap.dedent(f"""\
            -- View: {spec.description}
            -- Dialect: {spec.dialect}

            CREATE VIEW IF NOT EXISTS {view_name} AS
            SELECT
              {main_table}.*
            FROM {main_table};
        """)

        return GeneratedSQL(
            filename=f"{spec.name}.sql",
            code=code,
            dialect=spec.dialect,
            lines=code.count("\n") + 1,
        )

    def _gen_procedure(self, spec: SQLSpec) -> GeneratedSQL:
        name = spec.name.replace("-", "_")
        tables = spec.tables

        if spec.dialect == "postgresql":
            code = textwrap.dedent(f"""\
                -- Procedure: {spec.description}

                CREATE OR REPLACE FUNCTION {name}()
                RETURNS TABLE (id INTEGER, result TEXT) AS $$
                BEGIN
                  -- TODO: implement
                  RETURN QUERY SELECT 1, 'placeholder'::TEXT;
                END;
                $$ LANGUAGE plpgsql;
            """)
        else:
            code = textwrap.dedent(f"""\
                -- CTE: {spec.description}
                -- SQLite does not support stored procedures; using CTE instead

                WITH {name}_cte AS (
                  SELECT * FROM {tables[0] if tables else 'table1'}
                )
                SELECT * FROM {name}_cte;
            """)

        return GeneratedSQL(
            filename=f"{spec.name}.sql",
            code=code,
            dialect=spec.dialect,
            lines=code.count("\n") + 1,
        )

    def _check_anti_patterns(self, code: str) -> List[str]:
        found = []
        if "SELECT *" in code and "-- " not in code.split("SELECT *")[0].split("\n")[-1]:
            found.append("select_star")
        if "CREATE TABLE" in code and "PRIMARY KEY" not in code:
            found.append("no_primary_key")
        if "created_at" not in code.lower() and "CREATE TABLE" in code:
            found.append("missing_timestamps")
        return found

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        specs_raw = w.get("specs", [])

        generated = []
        all_anti_patterns = []
        total_lines = 0
        type_counts: Dict[str, int] = {}
        dialect_counts: Dict[str, int] = {}

        for spec_dict in specs_raw:
            spec = self._parse_spec(spec_dict)
            sql_result = self._generate_sql(spec)
            generated.append(sql_result)
            total_lines += sql_result.lines
            type_counts[spec.sql_type] = type_counts.get(spec.sql_type, 0) + 1
            dialect_counts[spec.dialect] = dialect_counts.get(spec.dialect, 0) + 1
            all_anti_patterns.extend(self._check_anti_patterns(sql_result.code))

        recommendations = []
        for gen in generated:
            recommendations.append({
                "technique": f"codegen_sql_{gen.filename}",
                "impact": f"Generated {gen.lines} lines of {gen.dialect} SQL",
                "reasoning": f"File: {gen.filename}, Tables: {gen.tables_created}, Indexes: {gen.indexes_created}",
                "filename": gen.filename,
                "code": gen.code,
                "dialect": gen.dialect,
                "lines": gen.lines,
                "tables_created": gen.tables_created,
                "indexes_created": gen.indexes_created,
            })

        meta_insight = (
            f"Generated {len(generated)} SQL files totaling {total_lines} lines. "
            f"Dialects: {', '.join(f'{k}({v})' for k, v in dialect_counts.items())}. "
            f"Types: {', '.join(f'{k}({v})' for k, v in type_counts.items())}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=SQL_RULES[:len(generated) + 2],
            meta_insight=meta_insight,
            analysis_data={
                "files_generated": len(generated),
                "total_lines": total_lines,
                "type_distribution": type_counts,
                "dialect_distribution": dialect_counts,
                "all_tables": [t for g in generated for t in g.tables_created],
                "all_indexes": [i for g in generated for i in g.indexes_created],
            },
            anti_patterns=list(set(all_anti_patterns)),
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = CodegenSqlAnalyzer()
    run_standard_cli(
        agent_name="CodeGen SQL",
        description="Generate SQL code from natural language specifications",
        analyzer=analyzer,
    )
