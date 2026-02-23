"""Manage Node.js mock servers spawned from OpenAPI specs.

Each project can have one mock server running at a time.  The server is a
self-contained Node.js HTTP server that uses only stdlib (http, url, fs)
and responds with deterministic mock data based on the OpenAPI schema.
"""
import json
import os
import signal
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Any

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "mock_server_template.js"

# In-memory registry of running servers: project_id -> server info
_active_servers: dict[str, dict[str, Any]] = {}

# Port range for mock servers
_PORT_MIN = 9100
_PORT_MAX = 9199


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_mock_server(project_id: str, openapi_spec: dict) -> dict:
    """Spawn a Node.js mock server for a project.

    Returns a dict with { running, port, pid } on success,
    or { running: False, error: str } on failure.
    """
    # Stop any existing server for this project
    if project_id in _active_servers:
        stop_mock_server(project_id)

    port = _find_free_port()
    if port is None:
        return {"running": False, "error": "No free ports in range 9100-9199"}

    # Generate the mock server code
    routes = _spec_to_routes(openapi_spec)
    server_code = _generate_mock_server_code(routes, port)

    # Write to a temp file
    tmp = tempfile.NamedTemporaryFile(
        suffix=".js", prefix=f"mock_{project_id[:8]}_",
        delete=False, mode="w",
    )
    tmp.write(server_code)
    tmp.close()

    try:
        process = subprocess.Popen(
            ["node", tmp.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "PORT": str(port)},
        )

        _active_servers[project_id] = {
            "process": process,
            "port": port,
            "pid": process.pid,
            "file": tmp.name,
        }

        return {"running": True, "port": port, "pid": process.pid}

    except FileNotFoundError:
        # Node.js not installed
        os.unlink(tmp.name)
        return {"running": False, "error": "Node.js not found. Install Node.js to use mock servers."}
    except Exception as e:
        os.unlink(tmp.name)
        return {"running": False, "error": str(e)}


def stop_mock_server(project_id: str) -> dict:
    """Stop the mock server for a project."""
    info = _active_servers.pop(project_id, None)
    if info is None:
        return {"running": False}

    process = info.get("process")
    if process:
        try:
            # Try graceful shutdown first
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        except Exception:
            # Process may have already exited
            try:
                os.kill(info["pid"], signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass

    # Clean up temp file
    tmp_file = info.get("file")
    if tmp_file and os.path.exists(tmp_file):
        try:
            os.unlink(tmp_file)
        except OSError:
            pass

    return {"running": False}


def get_mock_status(project_id: str) -> dict:
    """Check if a mock server is running for a project."""
    info = _active_servers.get(project_id)
    if info is None:
        return {"running": False, "port": None, "pid": None}

    process = info.get("process")
    if process and process.poll() is not None:
        # Process has exited
        _active_servers.pop(project_id, None)
        return {"running": False, "port": None, "pid": None, "exit_code": process.returncode}

    return {
        "running": True,
        "port": info["port"],
        "pid": info["pid"],
    }


def update_mock_server(project_id: str, openapi_spec: dict) -> dict:
    """Restart mock server with updated routes."""
    stop_mock_server(project_id)
    return start_mock_server(project_id, openapi_spec)


def stop_all():
    """Stop all running mock servers. Called on application shutdown."""
    for project_id in list(_active_servers.keys()):
        stop_mock_server(project_id)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_free_port() -> int | None:
    """Find a free port in the configured range."""
    used_ports = {info["port"] for info in _active_servers.values()}

    for port in range(_PORT_MIN, _PORT_MAX + 1):
        if port in used_ports:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue

    return None


def _spec_to_routes(spec: dict) -> list[dict]:
    """Convert OpenAPI paths to a simplified route list for the JS template."""
    routes = []
    schemas = spec.get("components", {}).get("schemas", {})

    for path, methods in spec.get("paths", {}).items():
        for method, operation in methods.items():
            if not isinstance(operation, dict):
                continue

            # Generate mock response data
            response_data = _generate_mock_response(operation, schemas)

            # Convert OpenAPI path params {id} to Express-style :id
            js_path = path.replace("{", ":").replace("}", "")

            routes.append({
                "method": method.upper(),
                "path": js_path,
                "summary": operation.get("summary", ""),
                "response": response_data,
                "status": 200 if method.lower() != "delete" else 204,
            })

    return routes


def _generate_mock_response(operation: dict, schemas: dict) -> Any:
    """Generate deterministic mock data for an API response."""
    responses = operation.get("responses", {})

    # Try to find a 200/201 response with a schema
    for code in ("200", "201", "default"):
        resp = responses.get(code, {})
        content = resp.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})

        if schema:
            return _mock_from_schema(schema, schemas, depth=0)

    # Fallback: generic success response
    return {"message": "OK", "status": "success"}


def _mock_from_schema(schema: dict, schemas: dict, depth: int = 0) -> Any:
    """Generate mock data from an OpenAPI schema."""
    if depth > 5:
        return None

    # Handle $ref
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        if ref_name in schemas:
            return _mock_from_schema(schemas[ref_name], schemas, depth + 1)
        return {"id": 1, "name": ref_name}

    schema_type = schema.get("type", "object")

    if schema_type == "string":
        if schema.get("format") == "date-time":
            return "2025-01-15T10:30:00Z"
        if schema.get("format") == "email":
            return "user@example.com"
        if schema.get("format") == "uri":
            return "https://example.com"
        if "enum" in schema:
            return schema["enum"][0]
        # Use property-name heuristics from example field
        example = schema.get("example")
        if example:
            return example
        return "mock-string-value"

    elif schema_type == "integer":
        return schema.get("example", 42)

    elif schema_type == "number":
        return schema.get("example", 3.14)

    elif schema_type == "boolean":
        return schema.get("example", True)

    elif schema_type == "array":
        items = schema.get("items", {})
        item = _mock_from_schema(items, schemas, depth + 1)
        return [item] if item is not None else []

    elif schema_type == "object":
        obj = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            obj[prop_name] = _mock_from_schema(prop_schema, schemas, depth + 1)
        if not obj:
            return {"id": 1, "name": "example"}
        return obj

    return None


def _generate_mock_server_code(routes: list[dict], port: int) -> str:
    """Generate a self-contained Node.js mock server from routes."""
    # Try to load the template
    if TEMPLATE_PATH.exists():
        template = TEMPLATE_PATH.read_text()
        routes_json = json.dumps(routes, indent=2)
        return template.replace("__ROUTES_PLACEHOLDER__", routes_json).replace("__PORT_PLACEHOLDER__", str(port))

    # Inline fallback if template file is missing
    routes_json = json.dumps(routes, indent=2)
    return f"""\
const http = require('http');
const url = require('url');

const PORT = {port};
const ROUTES = {routes_json};

function matchRoute(method, pathname) {{
  for (const route of ROUTES) {{
    if (route.method !== method) continue;
    const routeParts = route.path.split('/');
    const pathParts = pathname.split('/');
    if (routeParts.length !== pathParts.length) continue;
    const params = {{}};
    let match = true;
    for (let i = 0; i < routeParts.length; i++) {{
      if (routeParts[i].startsWith(':')) {{
        params[routeParts[i].slice(1)] = pathParts[i];
      }} else if (routeParts[i] !== pathParts[i]) {{
        match = false;
        break;
      }}
    }}
    if (match) return {{ route, params }};
  }}
  return null;
}}

const server = http.createServer((req, res) => {{
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {{ res.writeHead(204); return res.end(); }}

  const parsed = url.parse(req.url, true);
  const result = matchRoute(req.method, parsed.pathname);
  if (result) {{
    const {{ route, params }} = result;
    res.writeHead(route.status || 200, {{ 'Content-Type': 'application/json' }});
    const body = typeof route.response === 'object'
      ? JSON.stringify(route.response)
      : JSON.stringify({{ data: route.response }});
    res.end(body);
  }} else {{
    res.writeHead(404, {{ 'Content-Type': 'application/json' }});
    res.end(JSON.stringify({{ error: 'Not Found', path: parsed.pathname }}));
  }}
}});

server.listen(PORT, () => {{
  console.log('Mock server running on http://localhost:' + PORT);
  console.log('Routes: ' + ROUTES.length);
}});
"""
