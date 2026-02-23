"""Generate TypeScript interfaces from OpenAPI spec schemas.

Takes an OpenAPI 3.0 spec dict (specifically the components/schemas section)
and produces TypeScript interface declarations.
"""
from typing import Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_typescript_types(openapi_spec: dict) -> str:
    """Generate TypeScript interfaces from OpenAPI spec schemas.

    Returns a string of TypeScript code with exported interfaces.
    """
    lines: list[str] = [
        "// Auto-generated TypeScript types",
        "// Generated from OpenAPI spec by Studio type generator",
        "",
    ]

    schemas = openapi_spec.get("components", {}).get("schemas", {})
    if not schemas:
        lines.append("// No schemas found in the API spec.")
        return "\n".join(lines)

    for name, schema in schemas.items():
        lines.extend(_schema_to_interface(name, schema))
        lines.append("")

    # Also generate API endpoint types if paths are present
    paths = openapi_spec.get("paths", {})
    if paths:
        lines.append("// --- API Endpoint Types ---")
        lines.append("")
        lines.extend(_generate_api_types(paths))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Schema to TypeScript interface
# ---------------------------------------------------------------------------

def _schema_to_interface(name: str, schema: dict) -> list[str]:
    """Convert a single OpenAPI schema to a TypeScript interface."""
    lines: list[str] = []
    required_fields = set(schema.get("required", []))

    # Handle enums
    if "enum" in schema:
        values = " | ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in schema["enum"])
        lines.append(f"export type {name} = {values};")
        return lines

    # Handle allOf (inheritance)
    if "allOf" in schema:
        extends = []
        props_schema: dict[str, Any] = {"properties": {}, "required": []}
        for sub in schema["allOf"]:
            if "$ref" in sub:
                ref_name = sub["$ref"].split("/")[-1]
                extends.append(ref_name)
            else:
                props_schema["properties"].update(sub.get("properties", {}))
                props_schema["required"].extend(sub.get("required", []))

        extends_str = f" extends {', '.join(extends)}" if extends else ""
        lines.append(f"export interface {name}{extends_str} {{")

        required_fields = set(props_schema.get("required", []))
        for prop_name, prop_schema in props_schema.get("properties", {}).items():
            ts_type = _openapi_to_ts_type(prop_schema)
            optional = "" if prop_name in required_fields else "?"
            lines.append(f"  {prop_name}{optional}: {ts_type};")

        lines.append("}")
        return lines

    # Standard object
    lines.append(f"export interface {name} {{")

    properties = schema.get("properties", {})
    for prop_name, prop_schema in properties.items():
        ts_type = _openapi_to_ts_type(prop_schema)
        optional = "" if prop_name in required_fields else "?"
        description = prop_schema.get("description", "")
        if description:
            lines.append(f"  /** {description} */")
        lines.append(f"  {prop_name}{optional}: {ts_type};")

    # If no properties, add index signature
    if not properties and schema.get("type") == "object":
        lines.append("  [key: string]: unknown;")

    lines.append("}")
    return lines


# ---------------------------------------------------------------------------
# OpenAPI type to TypeScript type mapping
# ---------------------------------------------------------------------------

def _openapi_to_ts_type(prop_schema: dict) -> str:
    """Convert an OpenAPI property schema to a TypeScript type string."""
    if not isinstance(prop_schema, dict):
        return "unknown"

    # Handle $ref
    if "$ref" in prop_schema:
        return prop_schema["$ref"].split("/")[-1]

    # Handle oneOf / anyOf
    for key in ("oneOf", "anyOf"):
        if key in prop_schema:
            types = [_openapi_to_ts_type(s) for s in prop_schema[key]]
            return " | ".join(types)

    schema_type = prop_schema.get("type", "")
    nullable = prop_schema.get("nullable", False)

    if schema_type == "string":
        # Check for enum
        if "enum" in prop_schema:
            ts = " | ".join(f'"{v}"' for v in prop_schema["enum"])
        elif prop_schema.get("format") == "date-time":
            ts = "string"  # ISO date string
        else:
            ts = "string"
    elif schema_type == "integer" or schema_type == "number":
        ts = "number"
    elif schema_type == "boolean":
        ts = "boolean"
    elif schema_type == "array":
        items = prop_schema.get("items", {})
        item_type = _openapi_to_ts_type(items)
        ts = f"{item_type}[]"
    elif schema_type == "object":
        # Check for additionalProperties (Record type)
        additional = prop_schema.get("additionalProperties")
        if additional and isinstance(additional, dict):
            value_type = _openapi_to_ts_type(additional)
            ts = f"Record<string, {value_type}>"
        elif "properties" in prop_schema:
            # Inline object
            parts = []
            required = set(prop_schema.get("required", []))
            for k, v in prop_schema["properties"].items():
                opt = "" if k in required else "?"
                parts.append(f"{k}{opt}: {_openapi_to_ts_type(v)}")
            ts = "{ " + "; ".join(parts) + " }"
        else:
            ts = "Record<string, unknown>"
    else:
        ts = "unknown"

    if nullable:
        ts = f"{ts} | null"

    return ts


# ---------------------------------------------------------------------------
# Generate API endpoint helper types
# ---------------------------------------------------------------------------

def _generate_api_types(paths: dict) -> list[str]:
    """Generate request/response types from API paths."""
    lines: list[str] = []

    for path, methods in paths.items():
        for method, operation in methods.items():
            if not isinstance(operation, dict):
                continue

            op_id = operation.get("operationId", "")
            if not op_id:
                # Generate from path + method
                safe_path = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
                op_id = f"{method}_{safe_path}"

            type_name = _to_pascal_case(op_id)

            # Request params type
            params = operation.get("parameters", [])
            if params:
                lines.append(f"export interface {type_name}Params {{")
                for p in params:
                    if not isinstance(p, dict):
                        continue
                    name = p.get("name", "param")
                    schema = p.get("schema", {"type": "string"})
                    ts_type = _openapi_to_ts_type(schema)
                    optional = "" if p.get("required", False) else "?"
                    lines.append(f"  {name}{optional}: {ts_type};")
                lines.append("}")
                lines.append("")

            # Request body type
            body = operation.get("requestBody", {})
            if body:
                content = body.get("content", {})
                json_content = content.get("application/json", {})
                body_schema = json_content.get("schema", {})
                if body_schema and "$ref" not in body_schema:
                    lines.append(f"export interface {type_name}Body {{")
                    for prop_name, prop_schema in body_schema.get("properties", {}).items():
                        ts_type = _openapi_to_ts_type(prop_schema)
                        lines.append(f"  {prop_name}?: {ts_type};")
                    lines.append("}")
                    lines.append("")

    return lines


def _to_pascal_case(s: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    return "".join(
        word.capitalize() for word in s.replace("-", "_").split("_")
    )
