"""Extract OpenAPI-like spec from AI-generated FastAPI / Express code.

Uses AST parsing for Python and regex fallback for other languages.
This is best-effort extraction -- generated code may not always be parseable.
"""
import ast
import re
import json
from typing import Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_openapi_from_code(code: str) -> dict:
    """Parse Python/FastAPI code and extract an OpenAPI 3.0-like spec.

    Detects:
      - Route decorators: @app.get("/path"), @router.post("/path"), etc.
      - Pydantic models (class Name(BaseModel): ...)
      - Function signatures for request/response hints

    Returns a dict conforming (loosely) to the OpenAPI 3.0 structure.
    """
    spec: dict[str, Any] = {
        "openapi": "3.0.0",
        "info": {"title": "Generated API", "version": "1.0.0"},
        "paths": {},
        "components": {"schemas": {}},
    }

    # Try AST-based extraction first
    try:
        tree = ast.parse(code)
        _extract_routes_ast(tree, spec)
        _extract_models_ast(tree, spec)
    except SyntaxError:
        # Fall back to regex
        _extract_routes_regex(code, spec)
        _extract_models_regex(code, spec)

    return spec


# ---------------------------------------------------------------------------
# AST-based extraction (Python / FastAPI)
# ---------------------------------------------------------------------------

def _extract_routes_ast(tree: ast.Module, spec: dict):
    """Walk AST and find decorated route handlers."""
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            method, path = _parse_route_decorator(decorator)
            if method is None or path is None:
                continue

            # Build operation
            operation: dict[str, Any] = {
                "summary": _docstring(node) or node.name.replace("_", " ").title(),
                "operationId": node.name,
                "responses": {
                    "200": {"description": "Successful response"},
                },
            }

            # Extract parameters from function signature
            params = _extract_params_from_func(node)
            if params:
                operation["parameters"] = params

            # Extract request body hint from type annotations
            body_schema = _extract_body_from_func(node)
            if body_schema:
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": body_schema,
                        },
                    },
                }

            path_key = path if path.startswith("/") else f"/{path}"
            spec["paths"].setdefault(path_key, {})
            spec["paths"][path_key][method] = operation


def _parse_route_decorator(decorator: ast.expr):
    """Parse @app.get("/path") or @router.post("/path") style decorators."""
    if not isinstance(decorator, ast.Call):
        return None, None

    func = decorator.func
    if not isinstance(func, ast.Attribute):
        return None, None

    method = func.attr.lower()
    if method not in ("get", "post", "put", "delete", "patch", "options", "head"):
        return None, None

    # First positional arg is the path
    if not decorator.args:
        return None, None

    path_node = decorator.args[0]
    if isinstance(path_node, ast.Constant) and isinstance(path_node.value, str):
        return method, path_node.value

    return None, None


def _docstring(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Extract the docstring from a function node."""
    if (
        node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        return node.body[0].value.value.strip()
    return None


def _extract_params_from_func(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict]:
    """Extract path/query parameters from function args."""
    params = []
    skip = {"self", "cls", "request", "req", "body", "db", "session"}

    for arg in node.args.args:
        name = arg.arg
        if name in skip:
            continue

        param: dict[str, Any] = {
            "name": name,
            "in": "query",
            "required": True,
            "schema": {"type": "string"},
        }

        # If arg has annotation, try to infer type
        if arg.annotation:
            ts = _annotation_to_schema(arg.annotation)
            if ts:
                param["schema"] = ts

        params.append(param)

    return params


def _extract_body_from_func(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict | None:
    """Check if any parameter is typed with a Pydantic model reference."""
    skip = {"self", "cls", "request", "req", "db", "session"}
    for arg in node.args.args:
        if arg.arg in skip:
            continue
        if arg.annotation and isinstance(arg.annotation, ast.Name):
            # Looks like a model reference (e.g., CreateUserRequest)
            name = arg.annotation.id
            if name[0].isupper() and name not in ("Request", "Response", "str", "int", "float", "bool", "list", "dict"):
                return {"$ref": f"#/components/schemas/{name}"}
    return None


def _annotation_to_schema(annotation: ast.expr) -> dict | None:
    """Convert a simple type annotation AST node to an OpenAPI schema."""
    if isinstance(annotation, ast.Name):
        mapping = {
            "str": {"type": "string"},
            "int": {"type": "integer"},
            "float": {"type": "number"},
            "bool": {"type": "boolean"},
            "list": {"type": "array", "items": {"type": "string"}},
            "dict": {"type": "object"},
        }
        return mapping.get(annotation.id)

    if isinstance(annotation, ast.Constant):
        if isinstance(annotation.value, str):
            return {"type": "string"}

    # Optional[X] or X | None
    if isinstance(annotation, ast.Subscript):
        if isinstance(annotation.value, ast.Name) and annotation.value.id == "Optional":
            inner = _annotation_to_schema(annotation.slice)
            if inner:
                inner["nullable"] = True
                return inner

    return None


def _extract_models_ast(tree: ast.Module, spec: dict):
    """Find Pydantic BaseModel subclasses and extract their fields."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        # Check if it inherits from BaseModel
        is_model = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "BaseModel":
                is_model = True
            elif isinstance(base, ast.Attribute) and base.attr == "BaseModel":
                is_model = True
        if not is_model:
            continue

        schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                field_schema = {"type": "string"}  # default

                if item.annotation:
                    inferred = _annotation_to_schema(item.annotation)
                    if inferred:
                        field_schema = inferred

                schema["properties"][field_name] = field_schema

                # If no default value, it's required
                if item.value is None:
                    schema["required"].append(field_name)

        if not schema["required"]:
            del schema["required"]

        spec["components"]["schemas"][node.name] = schema


# ---------------------------------------------------------------------------
# Regex fallback (for unparseable code or non-Python)
# ---------------------------------------------------------------------------

_ROUTE_RE = re.compile(
    r'@(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']\s*\)',
    re.IGNORECASE,
)

_FUNC_RE = re.compile(
    r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)',
)

_MODEL_RE = re.compile(
    r'class\s+(\w+)\s*\(\s*BaseModel\s*\)\s*:',
)

_FIELD_RE = re.compile(
    r'^\s+(\w+)\s*:\s*(\w[\w\[\], |]*)',
    re.MULTILINE,
)


def _extract_routes_regex(code: str, spec: dict):
    """Regex-based route extraction as fallback."""
    lines = code.split("\n")
    for i, line in enumerate(lines):
        m = _ROUTE_RE.search(line)
        if not m:
            continue

        method = m.group(1).lower()
        path = m.group(2)

        # Look for the next function def
        func_name = "unknown"
        for j in range(i + 1, min(i + 5, len(lines))):
            fm = _FUNC_RE.search(lines[j])
            if fm:
                func_name = fm.group(1)
                break

        path_key = path if path.startswith("/") else f"/{path}"
        spec["paths"].setdefault(path_key, {})
        spec["paths"][path_key][method] = {
            "summary": func_name.replace("_", " ").title(),
            "operationId": func_name,
            "responses": {"200": {"description": "Successful response"}},
        }


def _extract_models_regex(code: str, spec: dict):
    """Regex-based Pydantic model extraction as fallback."""
    for m in _MODEL_RE.finditer(code):
        model_name = m.group(1)
        # Find fields after the class definition
        start = m.end()
        # Find the next class or top-level def as boundary
        rest = code[start:]

        # Grab until next class/def at indent level 0
        block_end = len(rest)
        for bm in re.finditer(r'^(?:class |def |async def )', rest, re.MULTILINE):
            # Only break on non-indented definitions
            line_start = rest.rfind("\n", 0, bm.start()) + 1
            if line_start == bm.start() or rest[line_start:bm.start()].strip() == "":
                block_end = bm.start()
                break

        block = rest[:block_end]
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
        }

        for fm in _FIELD_RE.finditer(block):
            field_name = fm.group(1)
            field_type = fm.group(2).strip()
            schema["properties"][field_name] = _python_type_to_schema(field_type)

        if schema["properties"]:
            spec["components"]["schemas"][model_name] = schema


def _python_type_to_schema(type_str: str) -> dict:
    """Map a Python type string to an OpenAPI schema dict."""
    type_str = type_str.strip()
    mapping = {
        "str": {"type": "string"},
        "int": {"type": "integer"},
        "float": {"type": "number"},
        "bool": {"type": "boolean"},
        "list": {"type": "array", "items": {"type": "string"}},
        "dict": {"type": "object"},
        "List[str]": {"type": "array", "items": {"type": "string"}},
        "List[int]": {"type": "array", "items": {"type": "integer"}},
        "List[float]": {"type": "array", "items": {"type": "number"}},
        "Optional[str]": {"type": "string", "nullable": True},
        "Optional[int]": {"type": "integer", "nullable": True},
        "Optional[float]": {"type": "number", "nullable": True},
        "Optional[bool]": {"type": "boolean", "nullable": True},
    }
    return mapping.get(type_str, {"type": "string"})
