#!/usr/bin/env python3
"""Run all tests in the test suite with detailed summary output.

Usage:
    cd backend
    python -m tests.run_all           # from backend dir
    python tests/run_all.py           # from backend dir

    # Or from project root:
    python backend/tests/run_all.py
"""
import os
import sys
import time
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Set up paths so imports work regardless of working directory.
# ---------------------------------------------------------------------------
TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure env vars are set before any test imports
os.environ.setdefault("WORKSPACE_MODE", "standalone")
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("ANTHROPIC_API_KEY", "")


# ---------------------------------------------------------------------------
# Test module registry — ordered from fast/unit to slow/integration.
# ---------------------------------------------------------------------------
TEST_MODULES = [
    "tests.test_model_router",         # Unit — no API calls
    "tests.test_playbook_index",       # Unit — no API calls
    "tests.test_api_endpoints",        # Integration — FastAPI + some API calls
    "tests.test_gemini_service",       # Integration — live Gemini API
    "tests.test_claude_service",       # Integration — live Claude API
]


def _separator(char: str = "=", width: int = 72) -> str:
    return char * width


def main():
    print(_separator())
    print("  MULTI-AI AGENTIC WORKSPACE  --  TEST SUITE RUNNER")
    print(_separator())
    print()

    overall_start = time.time()
    loader = unittest.TestLoader()
    all_results = []
    total_run = 0
    total_pass = 0
    total_fail = 0
    total_error = 0
    total_skip = 0

    for module_name in TEST_MODULES:
        print(f"  [{module_name}]")
        print(_separator("-", 60))

        try:
            suite = loader.loadTestsFromName(module_name)
        except Exception as exc:
            print(f"    LOAD ERROR: {exc}")
            print()
            total_error += 1
            all_results.append((module_name, None, str(exc)))
            continue

        # Run with a buffered, verbose runner
        runner = unittest.TextTestRunner(
            verbosity=2,
            stream=sys.stdout,
        )
        start = time.time()
        result = runner.run(suite)
        elapsed = time.time() - start

        run = result.testsRun
        fail = len(result.failures)
        err = len(result.errors)
        skip = len(result.skipped)
        passed = run - fail - err - skip

        total_run += run
        total_pass += passed
        total_fail += fail
        total_error += err
        total_skip += skip

        all_results.append((module_name, result, f"{elapsed:.2f}s"))
        print(f"    -> {run} run, {passed} passed, {fail} failed, {err} errors, {skip} skipped ({elapsed:.2f}s)")
        print()

    overall_elapsed = time.time() - overall_start

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    print()
    print(_separator())
    print("  SUMMARY")
    print(_separator())
    print()
    print(f"  Modules tested : {len(TEST_MODULES)}")
    print(f"  Total tests    : {total_run}")
    print(f"  Passed         : {total_pass}")
    print(f"  Failed         : {total_fail}")
    print(f"  Errors         : {total_error}")
    print(f"  Skipped        : {total_skip}")
    print(f"  Time           : {overall_elapsed:.2f}s")
    print()

    # Per-module breakdown
    print("  Per-module breakdown:")
    print("  " + "-" * 60)
    for module_name, result, timing in all_results:
        if result is None:
            status = "LOAD_ERROR"
        elif result.failures or result.errors:
            status = "FAIL"
        else:
            status = "OK"
        print(f"    {status:12s}  {module_name:40s}  {timing}")
    print()

    # Final verdict
    if total_fail == 0 and total_error == 0:
        print("  RESULT: ALL TESTS PASSED")
        print(_separator())
        return 0
    else:
        print("  RESULT: SOME TESTS FAILED")
        print(_separator())

        # Print failure details
        if total_fail > 0 or total_error > 0:
            print()
            print("  FAILURE DETAILS:")
            print("  " + "-" * 60)
            for module_name, result, _ in all_results:
                if result is None:
                    continue
                for test_case, traceback_str in result.failures:
                    print(f"  FAIL: {test_case}")
                    for line in traceback_str.strip().split("\n"):
                        print(f"    {line}")
                    print()
                for test_case, traceback_str in result.errors:
                    print(f"  ERROR: {test_case}")
                    for line in traceback_str.strip().split("\n"):
                        print(f"    {line}")
                    print()

        return 1


if __name__ == "__main__":
    sys.exit(main())
