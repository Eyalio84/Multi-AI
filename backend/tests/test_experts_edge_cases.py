"""Comprehensive edge-case test suite for Expert + KG-OS endpoints.

Uses only stdlib (urllib) — no external dependencies needed.

Covers:
  1. Expert CRUD — invalid inputs, missing fields, empty payloads, duplicate ops
  2. Conversation lifecycle — orphan conversations, missing IDs, cascade delete
  3. KG-OS query engine — empty queries, nonexistent DBs, bad node IDs, boundary weights
  4. Route ordering — ensure /kgos/* doesn't get captured by /{expert_id}
  5. SQL injection attempts
  6. Unicode & special characters
  7. Concurrent-ish operations (rapid create/delete)
  8. Boundary values (very long strings, extreme floats, negative limits)
  9. Intent classifier coverage (all 14 categories)
  10. Pydantic validation (wrong types, extra fields)
  11. Internal engine methods (want_to, can_it, trace_path, explore_smart, etc.)
  12. Expert update edge cases
  13. Expert chat SSE edge cases
  14. List ordering
"""
import sys, os, json, time
import urllib.request
import urllib.error
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = "http://localhost:8000/api/experts"
KGOS = f"{BASE}/kgos"
VALID_DB = "claude-code-tools-kg"

passed = 0
failed = 0
errors = []


def http(method: str, url: str, body: dict | str | None = None, expect_stream: bool = False):
    """Minimal HTTP client using urllib. Returns (status_code, parsed_json_or_None)."""
    # URL-encode the path to handle special characters
    parsed = urllib.parse.urlparse(url)
    safe_path = urllib.parse.quote(parsed.path, safe="/:@")
    safe_url = urllib.parse.urlunparse(parsed._replace(path=safe_path))

    data = None
    headers = {}
    if body is not None:
        if isinstance(body, str):
            data = body.encode()
        else:
            data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(safe_url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read().decode()
        try:
            return resp.status, json.loads(raw)
        except json.JSONDecodeError:
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode() if e.fp else ""
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except Exception as e:
        # Connection errors, invalid URL, etc.
        return 0, str(e)


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  \u2713 {name}")
    else:
        failed += 1
        msg = f"  \u2717 {name}" + (f" \u2014 {detail}" if detail else "")
        print(msg)
        errors.append(msg)


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ══════════════════════════════════════════════════════════════
# 1. EXPERT CRUD — EDGE CASES
# ══════════════════════════════════════════════════════════════
section("1. Expert CRUD Edge Cases")

# 1a. Create with minimal fields
s, d = http("POST", BASE, {"name": "Minimal", "kg_db_id": VALID_DB})
check("Create with minimal fields → 200", s == 200, f"status={s}")
minimal_id = d.get("id", "") if isinstance(d, dict) else ""
check("Minimal expert has default alpha=0.35", isinstance(d, dict) and d.get("retrieval_alpha") == 0.35)
check("Minimal expert icon default 'brain'", isinstance(d, dict) and d.get("icon") == "brain")
check("Minimal expert color default", isinstance(d, dict) and d.get("color") == "#0ea5e9")

# 1b. Create with empty name
s, d = http("POST", BASE, {"name": "", "kg_db_id": VALID_DB})
check("Create with empty name succeeds", s == 200, f"status={s}")
empty_name_id = d.get("id", "") if isinstance(d, dict) else ""

# 1c. Create without required field kg_db_id
s, d = http("POST", BASE, {"name": "NoKG"})
check("Create without kg_db_id \u2192 422", s == 422, f"status={s}")

# 1d. Create without required field name
s, d = http("POST", BASE, {"kg_db_id": VALID_DB})
check("Create without name \u2192 422", s == 422, f"status={s}")

# 1e. Create with empty body
s, d = http("POST", BASE, {})
check("Create with empty body \u2192 422", s == 422, f"status={s}")

# 1f. Create with extra unknown fields
s, d = http("POST", BASE, {"name": "Extra", "kg_db_id": VALID_DB, "unknown_field": "hello", "foo": 42})
check("Create with extra fields succeeds (ignored)", s == 200, f"status={s}")
extra_id = d.get("id", "") if isinstance(d, dict) else ""

# 1g. GET nonexistent expert
s, d = http("GET", f"{BASE}/nonexistent-id-999")
check("GET nonexistent expert \u2192 404", s == 404, f"status={s}")

# 1h. UPDATE nonexistent expert
s, d = http("PUT", f"{BASE}/nonexistent-id-999", {"name": "Ghost"})
check("UPDATE nonexistent expert \u2192 404", s == 404, f"status={s}")

# 1i. DELETE nonexistent expert (idempotent)
s, d = http("DELETE", f"{BASE}/nonexistent-id-999")
check("DELETE nonexistent expert \u2192 200 (idempotent)", s == 200, f"status={s}")

# 1j. UPDATE with empty body (no changes)
s, d = http("PUT", f"{BASE}/{minimal_id}", {})
check("UPDATE with empty body \u2192 returns existing", s == 200)
check("Existing name unchanged", isinstance(d, dict) and d.get("name") == "Minimal")

# 1k. UPDATE only one field
s, d = http("PUT", f"{BASE}/{minimal_id}", {"description": "Updated desc"})
check("UPDATE single field succeeds", s == 200)
check("Description updated", isinstance(d, dict) and d.get("description") == "Updated desc")
check("Name preserved", isinstance(d, dict) and d.get("name") == "Minimal")

# 1l. DUPLICATE nonexistent expert
s, d = http("POST", f"{BASE}/nonexistent-id-999/duplicate")
check("DUPLICATE nonexistent \u2192 404", s == 404, f"status={s}")

# 1m. DUPLICATE then delete original — copy persists
s, d = http("POST", f"{BASE}/{minimal_id}/duplicate")
check("DUPLICATE succeeds", s == 200)
dup_id = d.get("id", "") if isinstance(d, dict) else ""
check("Duplicate has (Copy) suffix", isinstance(d, dict) and "(Copy)" in d.get("name", ""))
http("DELETE", f"{BASE}/{minimal_id}")
s, d = http("GET", f"{BASE}/{dup_id}")
check("Copy survives original deletion", s == 200)
check("Copy retains description", isinstance(d, dict) and d.get("description") == "Updated desc")

# 1n. Rapid creates — unique IDs
ids = set()
for i in range(10):
    s, d = http("POST", BASE, {"name": f"Rapid-{i}", "kg_db_id": VALID_DB})
    if s == 200 and isinstance(d, dict):
        ids.add(d["id"])
check(f"10 rapid creates \u2192 10 unique IDs", len(ids) == 10, f"got {len(ids)}")

# Cleanup rapid creates
for eid in ids:
    http("DELETE", f"{BASE}/{eid}")


# ══════════════════════════════════════════════════════════════
# 2. UNICODE & SPECIAL CHARACTERS
# ══════════════════════════════════════════════════════════════
section("2. Unicode & Special Characters")

s, d = http("POST", BASE, {"name": "\u65e5\u672c\u8a9e\u30a8\u30ad\u30b9\u30d1\u30fc\u30c8", "kg_db_id": VALID_DB, "description": "\u00d1o\u00f1o \u2192 \u00e0\u00e7c\u00e9\u00f1t"})
check("Create with unicode name", s == 200)
unicode_id = d.get("id", "") if isinstance(d, dict) else ""
s2, d2 = http("GET", f"{BASE}/{unicode_id}")
check("Unicode name preserved on GET", isinstance(d2, dict) and d2.get("name") == "\u65e5\u672c\u8a9e\u30a8\u30ad\u30b9\u30d1\u30fc\u30c8")
check("Accented description preserved", isinstance(d2, dict) and d2.get("description") == "\u00d1o\u00f1o \u2192 \u00e0\u00e7c\u00e9\u00f1t")

s, d = http("POST", BASE, {"name": "<script>alert('xss')</script>", "kg_db_id": VALID_DB})
check("HTML injection in name stored safely", s == 200)
xss_id = d.get("id", "") if isinstance(d, dict) else ""
s2, d2 = http("GET", f"{BASE}/{xss_id}")
check("Script tag returned as-is", isinstance(d2, dict) and "<script>" in d2.get("name", ""))

long_name = "A" * 5000
s, d = http("POST", BASE, {"name": long_name, "kg_db_id": VALID_DB})
check("Very long name (5000 chars) accepted", s == 200)
long_id = d.get("id", "") if isinstance(d, dict) else ""

for eid in [unicode_id, xss_id, long_id, empty_name_id, extra_id]:
    if eid:
        http("DELETE", f"{BASE}/{eid}")


# ══════════════════════════════════════════════════════════════
# 3. SQL INJECTION ATTEMPTS
# ══════════════════════════════════════════════════════════════
section("3. SQL Injection Attempts")

s, d = http("POST", BASE, {"name": "'; DROP TABLE experts; --", "kg_db_id": VALID_DB})
check("SQL injection in name \u2192 no crash", s == 200)
sqli_id = d.get("id", "") if isinstance(d, dict) else ""

s2, d2 = http("GET", BASE)
check("Experts table still exists after injection", s2 == 200 and isinstance(d2, list))

# URL with special chars may be rejected by HTTP client — that's fine (protection at client level)
s, d = http("GET", f"{BASE}/%27;%20DROP%20TABLE%20experts;%20--")
check("SQL injection in GET path \u2192 not 500", s != 500, f"status={s}")

s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "'; DROP TABLE nodes; --"})
check("SQL injection in KGOS query \u2192 no crash", s in (200, 400), f"status={s}")

s, d = http("POST", f"{KGOS}/query/%27;%20DROP%20TABLE%20nodes;%20--", {"query": "test"})
check("SQL injection in db_id path \u2192 400", s == 400, f"status={s}")

if sqli_id:
    http("DELETE", f"{BASE}/{sqli_id}")


# ══════════════════════════════════════════════════════════════
# 4. CONVERSATION LIFECYCLE
# ══════════════════════════════════════════════════════════════
section("4. Conversation Lifecycle")

s, d = http("POST", BASE, {"name": "ConvTest", "kg_db_id": VALID_DB})
conv_expert_id = d["id"] if isinstance(d, dict) else ""

s, d = http("GET", f"{BASE}/{conv_expert_id}/conversations")
check("Fresh expert has 0 conversations", s == 200 and d == [])

s, d = http("GET", f"{BASE}/{conv_expert_id}/conversations/fake-conv-id")
check("GET nonexistent conversation \u2192 404", s == 404)

s, d = http("DELETE", f"{BASE}/{conv_expert_id}/conversations/fake-conv-id")
check("DELETE nonexistent conversation \u2192 200", s == 200)

s, d = http("GET", f"{BASE}/fake-expert-id/conversations")
check("Conversations for nonexistent expert \u2192 200 (empty)", s == 200)

# Create conversation via service directly
from services.expert_service import ExpertService
svc = ExpertService()
svc._conn = None
conv = svc.create_conversation(conv_expert_id, title="Test Conv")
conv_id = conv["id"]
svc._log_message(conv_id, "user", "Hello")
svc._log_message(conv_id, "assistant", "Hi there")

s, d = http("GET", f"{BASE}/{conv_expert_id}/conversations")
check("Conversation created via service", s == 200 and len(d) == 1)

s, d = http("GET", f"{BASE}/{conv_expert_id}/conversations/{conv_id}")
check("Conversation has 2 messages", s == 200 and len(d.get("messages", [])) == 2)

# Delete expert and verify cascade
http("DELETE", f"{BASE}/{conv_expert_id}")
svc2 = ExpertService()
svc2._conn = None
conv_after = svc2.get_conversation(conv_id)
check("Cascade delete: conversation gone", conv_after is None)


# ══════════════════════════════════════════════════════════════
# 5. KG-OS QUERY ENGINE EDGE CASES
# ══════════════════════════════════════════════════════════════
section("5. KG-OS Query Engine Edge Cases")

# 5a. Empty query string
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": ""})
check("Empty query string \u2192 200", s == 200, f"status={s}")
check("Empty query returns 0 results", isinstance(d, dict) and d.get("total", -1) == 0)

# 5b. Very long query
long_query = "how do I " + " and ".join([f"do thing {i}" for i in range(200)])
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": long_query})
check("Very long query (200+ words) \u2192 no crash", s in (200, 400), f"status={s}")

# 5c. Nonexistent database
s, d = http("POST", f"{KGOS}/query/nonexistent-db-xyz", {"query": "test"})
check("Nonexistent DB \u2192 400", s == 400, f"status={s}")

# 5d. All-zero weights
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "read file", "alpha": 0, "beta": 0, "gamma": 0, "delta": 0})
check("All-zero weights \u2192 200 (0 results)", s == 200, f"status={s}")
check("Zero weights yield 0 results", isinstance(d, dict) and d.get("total", -1) == 0)

# 5e. Text-only weights
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "read file", "alpha": 0, "beta": 1.0, "gamma": 0, "delta": 0})
check("Text-only weights \u2192 200", s == 200)
if isinstance(d, dict) and d.get("total", 0) > 0:
    scores = d["results"][0]["scores"]
    check("Text-only: embedding score = 0", scores["embedding"] == 0)

# 5f. Negative weights
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "read file", "alpha": -0.5, "beta": 0.5, "gamma": 0, "delta": 0})
check("Negative alpha \u2192 handled gracefully", s == 200, f"status={s}")

# 5g. Limit = 0
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "read file", "limit": 0})
check("Limit=0 \u2192 0 results", s == 200 and isinstance(d, dict) and d.get("total") == 0)

# 5h. Limit = 1
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "read file", "limit": 1})
check("Limit=1 \u2192 at most 1 result", s == 200 and isinstance(d, dict) and d.get("total", 99) <= 1)

# 5i. Very large limit
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "read file", "limit": 10000})
check("Limit=10000 \u2192 no crash", s == 200)

# 5j. Impact on nonexistent node
s, d = http("POST", f"{KGOS}/impact/{VALID_DB}/nonexistent_node_xyz", {"direction": "forward", "max_depth": 2})
check("Impact nonexistent node \u2192 graceful", s in (200, 400))

# 5k. Impact direction=both
s, d = http("POST", f"{KGOS}/impact/{VALID_DB}/read_file", {"direction": "both", "max_depth": 1})
check("Impact direction=both \u2192 200", s == 200)

# 5l. Impact invalid direction
s, d = http("POST", f"{KGOS}/impact/{VALID_DB}/read_file", {"direction": "sideways", "max_depth": 1})
check("Impact invalid direction \u2192 handled", s in (200, 400))

# 5m. Similar nonexistent node
s, d = http("POST", f"{KGOS}/similar/{VALID_DB}/nonexistent_node_xyz")
check("Similar nonexistent node \u2192 graceful", s in (200, 400))

# 5n. Compose empty goal
s, d = http("POST", f"{KGOS}/compose/{VALID_DB}", {"goal": ""})
check("Compose empty goal \u2192 200", s == 200)

# 5o. Compose multi-step goal
s, d = http("POST", f"{KGOS}/compose/{VALID_DB}", {"goal": "read the file and then edit it and then run tests and commit and push", "max_steps": 10})
check("Compose multi-step \u2192 200", s == 200)
check("Multi-step decomposed \u2265 3 steps", isinstance(d, dict) and d.get("total_steps", 0) >= 3, f"steps={d.get('total_steps', 0) if isinstance(d, dict) else '?'}")

# 5p. Dimensions endpoint
s, d = http("GET", f"{KGOS}/dimensions")
check("Dimensions returns dict", s == 200 and isinstance(d, dict))
total_dims = sum(len(v) for v in d.values()) if isinstance(d, dict) else 0
check(f"Total dimensions = 56", total_dims == 56, f"got {total_dims}")
check("9 dimension categories", isinstance(d, dict) and len(d) == 9, f"got {len(d) if isinstance(d, dict) else '?'}")

# 5q. Weights summing to 4.0
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "read", "alpha": 1.0, "beta": 1.0, "gamma": 1.0, "delta": 1.0})
check("Weights summing to 4.0 \u2192 no crash", s == 200)

# 5r. Tiny weights
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "read", "alpha": 0.001, "beta": 0.001, "gamma": 0.001, "delta": 0.001})
check("Tiny weights \u2192 200", s == 200)

# 5s. Intent-only search
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "read a file", "alpha": 0, "beta": 0, "gamma": 0, "delta": 1.0, "methods": ["intent"]})
check("Intent-only search \u2192 200", s == 200)

# 5t. Empty methods list
s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "read", "methods": []})
check("Empty methods list \u2192 200 (0 results)", s == 200)


# ══════════════════════════════════════════════════════════════
# 6. ROUTE ORDERING
# ══════════════════════════════════════════════════════════════
section("6. Route Ordering Verification")

s, d = http("GET", f"{BASE}/kgos/dimensions")
check("/kgos/dimensions \u2192 200 (not captured by /{expert_id})", s == 200)
check("Returns dimensions dict, not expert", isinstance(d, dict) and "performance_cost" in d)

s, d = http("POST", f"{BASE}/kgos/query/{VALID_DB}", {"query": "test"})
check("/kgos/query \u2192 200 (not captured by expert route)", s == 200)

s, d = http("GET", f"{BASE}/kgos")
check("/experts/kgos alone \u2192 not 500", s != 500, f"status={s}")


# ══════════════════════════════════════════════════════════════
# 7. INTENT CLASSIFIER — ALL 14 CATEGORIES
# ══════════════════════════════════════════════════════════════
section("7. Intent Classifier \u2014 All 14 Categories")

from services.kgos_query_engine import kgos_query_engine

intent_tests = {
    "find_tool": "find a tool for reading files",
    "check_capability": "can Claude handle binary files?",
    "compose_workflow": "create a workflow to chain tools together",
    "compare": "compare Read vs Bash for file operations",
    "debug": "error when running the edit command",
    "optimize": "how to improve performance of searches",
    "learn": "explain how embeddings work",
    "explore": "show me everything about file operations",
    "impact": "what depends on the read_file node",
    "trace": "trace the path from read_file to edit_file",
    "recommend": "recommend the best tool for code review",
    "create": "create a new function for validation",
    "configure": "how to setup the environment variables",
    "security": "what are the authentication requirements",
}

for expected_intent, query in intent_tests.items():
    actual = kgos_query_engine.classify_intent(query)
    check(f"Intent '{expected_intent}' \u2190 \"{query[:45]}\"", actual == expected_intent, f"got '{actual}'")

# Classifier edge cases
check("Empty string \u2192 'explore' (default)", kgos_query_engine.classify_intent("") == "explore")
check("Single word 'error' \u2192 'debug'", kgos_query_engine.classify_intent("error") == "debug")
check("Numbers only \u2192 'explore'", kgos_query_engine.classify_intent("12345") == "explore")
check("'can Gemini support streaming?' \u2192 check_capability",
      kgos_query_engine.classify_intent("can Gemini support streaming?") == "check_capability")
check("Intent cache works (repeat query)", kgos_query_engine.classify_intent("error") == "debug")


# ══════════════════════════════════════════════════════════════
# 8. EXPERT UPDATE EDGE CASES
# ══════════════════════════════════════════════════════════════
section("8. Expert Update Edge Cases")

s, d = http("POST", BASE, {"name": "UpdateTest", "kg_db_id": VALID_DB})
upd_id = d["id"] if isinstance(d, dict) else ""

s, d = http("PUT", f"{BASE}/{upd_id}", {"retrieval_alpha": 0.50, "retrieval_beta": 0.30, "retrieval_gamma": 0.10, "retrieval_delta": 0.10})
check("Update all 4 weights", s == 200)
check("Alpha updated to 0.50", isinstance(d, dict) and d.get("retrieval_alpha") == 0.50)
check("Beta updated to 0.30", isinstance(d, dict) and d.get("retrieval_beta") == 0.30)

s, d = http("PUT", f"{BASE}/{upd_id}", {
    "retrieval_methods": ["text", "graph"],
    "dimension_filters": {"latency_sensitivity": {"min": 0.5}},
    "playbook_skills": ["cost-optimization", "extended-thinking"],
})
check("Update JSON fields", s == 200)
check("Methods updated", isinstance(d, dict) and d.get("retrieval_methods") == ["text", "graph"])
check("Dimension filters updated", isinstance(d, dict) and "latency_sensitivity" in d.get("dimension_filters", {}))
check("Playbook skills updated", isinstance(d, dict) and len(d.get("playbook_skills", [])) == 2)

s, d = http("PUT", f"{BASE}/{upd_id}", {"icon": "shield", "color": "#ff0000"})
check("Icon updated to shield", isinstance(d, dict) and d.get("icon") == "shield")
check("Color updated to red", isinstance(d, dict) and d.get("color") == "#ff0000")

s, d = http("PUT", f"{BASE}/{upd_id}", {"is_public": False})
check("is_public set to false", isinstance(d, dict) and d.get("is_public") in (False, 0))

s, d = http("PUT", f"{BASE}/{upd_id}", {"retrieval_alpha": "not_a_number"})
check("Wrong type for float \u2192 422", s == 422, f"status={s}")

http("DELETE", f"{BASE}/{upd_id}")


# ══════════════════════════════════════════════════════════════
# 9. EXPERT CHAT SSE EDGE CASES
# ══════════════════════════════════════════════════════════════
section("9. Expert Chat SSE Edge Cases")

s, d = http("POST", BASE, {"name": "ChatTest", "kg_db_id": VALID_DB})
chat_expert_id = d["id"] if isinstance(d, dict) else ""

s, d = http("POST", f"{BASE}/nonexistent-id/chat", {"query": "hello"})
check("Chat nonexistent expert \u2192 404", s == 404, f"status={s}")

# Chat with empty query — SSE stream
try:
    chat_url = f"{BASE}/{chat_expert_id}/chat"
    req = urllib.request.Request(
        chat_url,
        data=json.dumps({"query": ""}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=15)
    raw = resp.read(4096).decode()
    check("Chat empty query \u2192 200 SSE", resp.status == 200)
    check("SSE stream contains data: lines", "data:" in raw)
except urllib.error.HTTPError as e:
    check("Chat empty query \u2192 200 SSE", False, f"HTTP {e.code}")
except Exception as e:
    check("Chat empty query \u2192 no crash", False, str(e)[:80])

# Chat without query field
s, d = http("POST", f"{BASE}/{chat_expert_id}/chat", {})
check("Chat without query \u2192 422", s == 422, f"status={s}")

# Chat with history
try:
    chat_url2 = f"{BASE}/{chat_expert_id}/chat"
    req = urllib.request.Request(
        chat_url2,
        data=json.dumps({
            "query": "follow up",
            "history": [{"role": "user", "content": "hi"}, {"role": "model", "content": "hello"}]
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=15)
    raw = resp.read(4096).decode()
    check("Chat with history \u2192 200", resp.status == 200)
except urllib.error.HTTPError as e:
    check("Chat with history \u2192 200", False, f"HTTP {e.code}")
except Exception as e:
    check("Chat with history \u2192 no crash", False, str(e)[:80])

http("DELETE", f"{BASE}/{chat_expert_id}")


# ══════════════════════════════════════════════════════════════
# 10. KG-OS ENGINE INTERNAL METHODS
# ══════════════════════════════════════════════════════════════
section("10. KG-OS Engine Internal Methods")

# want_to
result = kgos_query_engine.want_to(VALID_DB, "read a file")
check("want_to returns results", len(result.get("results", [])) > 0)
check("want_to has goal field", result.get("goal") == "read a file")
check("want_to has keywords", len(result.get("keywords", [])) > 0)

result = kgos_query_engine.want_to(VALID_DB, "")
check("want_to empty goal \u2192 0 results", result.get("total", -1) == 0)

# can_it
result = kgos_query_engine.can_it(VALID_DB, "edit files")
check("can_it 'edit files' \u2192 supported=True", result.get("supported") == True)
check("can_it has limitations list", isinstance(result.get("limitations"), list))
check("can_it has workarounds list", isinstance(result.get("workarounds"), list))

result = kgos_query_engine.can_it(VALID_DB, "xyzzy zorch blarg plugh")
check("can_it gibberish \u2192 supported=False", result.get("supported") == False)

# trace_path
result = kgos_query_engine.trace_path(VALID_DB, "read_file", "edit_file", max_depth=5)
check("trace_path finds path", result.get("length", -1) > 0, f"length={result.get('length')}")
check("trace_path has edges list", isinstance(result.get("edges"), list))

result = kgos_query_engine.trace_path(VALID_DB, "read_file", "nonexistent_xyz", max_depth=3)
check("trace_path to nonexistent \u2192 no path", result.get("length", 0) <= 0)

result = kgos_query_engine.trace_path(VALID_DB, "nonexistent_source", "read_file", max_depth=3)
check("trace_path nonexistent source \u2192 error", "error" in result)

# explore_smart
result = kgos_query_engine.explore_smart(VALID_DB, "read_file", depth=2)
check("explore_smart returns levels", len(result.get("levels", [])) > 0)
check("explore_smart level has nodes", len(result["levels"][0].get("nodes", [])) > 0)
check("explore_smart nodes have degree", "degree" in result["levels"][0]["nodes"][0])
check("explore_smart total_explored > 0", result.get("total_explored", 0) > 0)

result = kgos_query_engine.explore_smart(VALID_DB, "nonexistent_xyz", depth=2)
check("explore_smart nonexistent \u2192 error", "error" in result)

# _keyword_match_nodes edge cases
result = kgos_query_engine._keyword_match_nodes(VALID_DB, "read%file")
check("Keyword match with % \u2192 no crash", isinstance(result, dict))

result = kgos_query_engine._keyword_match_nodes(VALID_DB, "'; DROP TABLE --")
check("Keyword match with SQL injection \u2192 no crash", isinstance(result, dict))

result = kgos_query_engine._keyword_match_nodes(VALID_DB, "")
check("Keyword match empty query \u2192 empty dict", result == {})


# ══════════════════════════════════════════════════════════════
# 11. PYDANTIC VALIDATION
# ══════════════════════════════════════════════════════════════
section("11. Pydantic Request Validation")

s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "test", "limit": "ten"})
check("Limit as string \u2192 422", s == 422, f"status={s}")

s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": "test", "alpha": "high"})
check("Alpha as string \u2192 422", s == 422, f"status={s}")

s, d = http("POST", f"{KGOS}/query/{VALID_DB}", {"query": ["a", "b"]})
check("Query as list \u2192 422", s == 422, f"status={s}")

s, d = http("POST", f"{KGOS}/compose/{VALID_DB}", {"goal": "test", "max_steps": 3})
check("Valid compose request \u2192 200", s == 200)

s, d = http("POST", f"{KGOS}/impact/{VALID_DB}/read_file", {"max_depth": "deep"})
check("max_depth as string \u2192 422", s == 422, f"status={s}")

s, d = http("POST", f"{KGOS}/query/{VALID_DB}")
check("POST without body \u2192 422", s == 422, f"status={s}")

s, d = http("POST", f"{KGOS}/query/{VALID_DB}", "not json")
check("Malformed JSON \u2192 422", s == 422, f"status={s}")


# ══════════════════════════════════════════════════════════════
# 12. CONCURRENT-ISH OPERATIONS
# ══════════════════════════════════════════════════════════════
section("12. Concurrent-ish Operations")

s, d = http("POST", BASE, {"name": "EphemeralExpert", "kg_db_id": VALID_DB})
eph_id = d["id"] if isinstance(d, dict) else ""
http("DELETE", f"{BASE}/{eph_id}")

s, d = http("GET", f"{BASE}/{eph_id}")
check("Access after delete \u2192 404", s == 404)

s, d = http("PUT", f"{BASE}/{eph_id}", {"name": "Ghost"})
check("Update after delete \u2192 404", s == 404)

s, d = http("POST", f"{BASE}/{eph_id}/duplicate")
check("Duplicate after delete \u2192 404", s == 404)

s, d = http("POST", f"{BASE}/{eph_id}/chat", {"query": "hello"})
check("Chat after delete \u2192 404", s == 404)


# ══════════════════════════════════════════════════════════════
# 13. LIST ORDERING
# ══════════════════════════════════════════════════════════════
section("13. List Ordering")

ids_ordered = []
for name in ["AAA-First", "BBB-Second", "CCC-Third"]:
    s, d = http("POST", BASE, {"name": name, "kg_db_id": VALID_DB})
    if isinstance(d, dict):
        ids_ordered.append(d["id"])
    time.sleep(0.15)

time.sleep(0.15)
http("PUT", f"{BASE}/{ids_ordered[0]}", {"description": "updated"})

s, d = http("GET", BASE)
test_experts = [e for e in d if isinstance(e, dict) and e.get("id") in ids_ordered] if isinstance(d, list) else []
check("All 3 test experts in list", len(test_experts) == 3)
if len(test_experts) >= 1:
    check("List ordered by updated_at DESC (most recent first)", test_experts[0]["name"] == "AAA-First",
          f"first={test_experts[0]['name']}")

for eid in ids_ordered:
    http("DELETE", f"{BASE}/{eid}")


# ══════════════════════════════════════════════════════════════
# 14. DOUBLE DUPLICATE
# ══════════════════════════════════════════════════════════════
section("14. Double Duplicate")

s, d = http("POST", BASE, {"name": "Original", "kg_db_id": VALID_DB})
orig_id = d["id"] if isinstance(d, dict) else ""

s, d = http("POST", f"{BASE}/{orig_id}/duplicate")
dup1_id = d["id"] if isinstance(d, dict) else ""
check("First duplicate name", isinstance(d, dict) and d.get("name") == "Original (Copy)")

s, d = http("POST", f"{BASE}/{dup1_id}/duplicate")
dup2_id = d["id"] if isinstance(d, dict) else ""
check("Double duplicate name", isinstance(d, dict) and d.get("name") == "Original (Copy) (Copy)")

for eid in [orig_id, dup1_id, dup2_id]:
    if eid:
        http("DELETE", f"{BASE}/{eid}")

# Final cleanup
s, d = http("GET", BASE)
if isinstance(d, list):
    for e in d:
        http("DELETE", f"{BASE}/{e['id']}")


# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
section("RESULTS")
total = passed + failed
print(f"\n  Passed: {passed}/{total}")
print(f"  Failed: {failed}/{total}")
if errors:
    print(f"\n  Failed tests:")
    for e in errors:
        print(f"    {e}")
print()
sys.exit(0 if failed == 0 else 1)
