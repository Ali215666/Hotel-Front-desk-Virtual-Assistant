"""
Hotel Front Desk AI — Benchmark & Stress Test Suite
====================================================
Tests three areas:
  1. Latency Benchmarking  — measures average / min / max response times
  2. Stress Testing        — fires N concurrent requests to find breaking points
  3. Failure Handling      — verifies correct behaviour under bad / edge inputs

Prerequisites
-------------
  pip install requests httpx websockets

Usage
-----
  # Make sure backend is running on localhost:8000, then:
  python tests/benchmark_tests.py

  # Run only one section:
  python tests/benchmark_tests.py --latency
  python tests/benchmark_tests.py --stress
  python tests/benchmark_tests.py --failure
"""

import argparse
import asyncio
import json
import statistics
import time
import uuid
from typing import Optional

import requests
import httpx

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL     = "http://localhost:8000"
WS_URL       = "ws://localhost:8000/ws/chat"
CHAT_ENDPOINT = f"{BASE_URL}/api/chat"
HEALTH_URL   = f"{BASE_URL}/health"

# ── Colours for terminal output ───────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):   print(f"  {GREEN}✔ {msg}{RESET}")
def warn(msg): print(f"  {YELLOW}⚠ {msg}{RESET}")
def fail(msg): print(f"  {RED}✘ {msg}{RESET}")
def info(msg): print(f"  {CYAN}→ {msg}{RESET}")
def header(title):
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")


# ══════════════════════════════════════════════════════════════════════════════
# Helper — single synchronous REST chat call
# ══════════════════════════════════════════════════════════════════════════════
def rest_chat(session_id: str, message: str, timeout: int = 90) -> dict:
    """
    Send one message to /api/chat.

    Returns a dict:
        {
          "status_code": int,
          "reply": str | None,
          "latency_ms": float,
          "error": str | None
        }
    """
    payload = {"session_id": session_id, "message": message}
    t0 = time.perf_counter()
    try:
        resp = requests.post(CHAT_ENDPOINT, json=payload, timeout=timeout)
        latency_ms = (time.perf_counter() - t0) * 1000
        if resp.status_code == 200:
            return {
                "status_code": resp.status_code,
                "reply": resp.json().get("reply"),
                "latency_ms": latency_ms,
                "error": None,
            }
        return {
            "status_code": resp.status_code,
            "reply": None,
            "latency_ms": latency_ms,
            "error": resp.text,
        }
    except requests.Timeout:
        return {"status_code": -1, "reply": None,
                "latency_ms": timeout * 1000, "error": "Timeout"}
    except requests.ConnectionError as e:
        return {"status_code": -1, "reply": None,
                "latency_ms": 0, "error": f"Connection refused: {e}"}


# ══════════════════════════════════════════════════════════════════════════════
# 1. LATENCY BENCHMARKING
# ══════════════════════════════════════════════════════════════════════════════
def run_latency_benchmark(num_requests: int = 5):
    """
    Send `num_requests` sequential messages and report timing statistics.

    Why sequential?  Concurrent requests saturate the single Ollama thread and
    inflate all numbers equally — sequential isolates per-request latency.
    """
    header("1 · LATENCY BENCHMARKING")
    info(f"Sending {num_requests} sequential requests to {CHAT_ENDPOINT}")

    # Check server reachability first
    try:
        h = requests.get(HEALTH_URL, timeout=5)
        ok(f"Backend health check passed ({h.status_code})")
    except Exception as e:
        fail(f"Backend not reachable: {e}")
        warn("Start the backend with:  uvicorn main:app --host 0.0.0.0 --port 8000")
        return

    session_id = f"bench-{uuid.uuid4()}"
    messages = [
        "Do you have rooms available this weekend?",
        "What is the check-in time?",
        "Does the hotel have a swimming pool?",
        "I need a room with a king bed for two nights.",
        "What is your cancellation policy?",
        "Is parking available at the hotel?",
        "Can I get a late checkout?",
    ]

    latencies   = []
    successes   = 0
    failures    = 0

    for i in range(num_requests):
        msg = messages[i % len(messages)]
        info(f"[{i+1}/{num_requests}] Sending: \"{msg[:50]}\"")
        result = rest_chat(session_id, msg)
        latencies.append(result["latency_ms"])

        if result["status_code"] == 200:
            successes += 1
            ok(f"  Reply in {result['latency_ms']:.0f} ms  →  "
               f"{str(result['reply'])[:80]}")
        else:
            failures += 1
            fail(f"  Failed ({result['status_code']}): {result['error'][:100]}")

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"\n  {'Metric':<22} {'Value':>10}")
    print(f"  {'─'*34}")
    print(f"  {'Requests sent':<22} {num_requests:>10}")
    print(f"  {'Successes':<22} {successes:>10}")
    print(f"  {'Failures':<22} {failures:>10}")
    if latencies:
        print(f"  {'Min latency (ms)':<22} {min(latencies):>10.0f}")
        print(f"  {'Max latency (ms)':<22} {max(latencies):>10.0f}")
        print(f"  {'Mean latency (ms)':<22} {statistics.mean(latencies):>10.0f}")
        if len(latencies) > 1:
            print(f"  {'Std dev (ms)':<22} {statistics.stdev(latencies):>10.0f}")

    if successes == num_requests:
        ok("All requests succeeded.")
    else:
        warn(f"{failures} request(s) failed — check Ollama logs.")


# ══════════════════════════════════════════════════════════════════════════════
# 2. STRESS TESTING (concurrent async requests)
# ══════════════════════════════════════════════════════════════════════════════
async def _async_chat(client: httpx.AsyncClient,
                      session_id: str,
                      message: str,
                      idx: int) -> dict:
    """Single async chat request."""
    payload = {"session_id": session_id, "message": message}
    t0 = time.perf_counter()
    try:
        resp = await client.post(CHAT_ENDPOINT, json=payload, timeout=120)
        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "idx": idx,
            "status_code": resp.status_code,
            "latency_ms": latency_ms,
            "reply": resp.json().get("reply") if resp.status_code == 200 else None,
            "error": resp.text if resp.status_code != 200 else None,
        }
    except httpx.TimeoutException:
        return {"idx": idx, "status_code": -1,
                "latency_ms": 120_000, "reply": None, "error": "Timeout"}
    except httpx.ConnectError as e:
        return {"idx": idx, "status_code": -1,
                "latency_ms": 0, "reply": None, "error": str(e)}


async def _stress_wave(concurrent_users: int):
    """Fire `concurrent_users` requests simultaneously and collect results."""
    messages = [
        "What rooms do you have available?",
        "I want to book a double room.",
        "What time is checkout?",
        "Do you have airport shuttle service?",
        "Is breakfast included?",
    ]
    tasks = []
    async with httpx.AsyncClient() as client:
        for i in range(concurrent_users):
            session_id = f"stress-{uuid.uuid4()}"
            msg = messages[i % len(messages)]
            tasks.append(_async_chat(client, session_id, msg, i))
        results = await asyncio.gather(*tasks)
    return results


def run_stress_test(max_users: int = 10, step: int = 2):
    """
    Incrementally ramp up concurrent users: step, step*2, ..., max_users.

    Reports success rate and mean latency at each concurrency level.
    """
    header("2 · STRESS TESTING")
    info(f"Ramping concurrent users: {step} → {max_users} (step={step})")

    # Check server first
    try:
        requests.get(HEALTH_URL, timeout=5)
        ok("Backend reachable.")
    except Exception as e:
        fail(f"Backend not reachable: {e}")
        return

    levels = list(range(step, max_users + 1, step))
    if max_users not in levels:
        levels.append(max_users)

    print(f"\n  {'Users':<8} {'Success':<10} {'Fail':<6} "
          f"{'Mean(ms)':<12} {'Max(ms)':<10} {'Min(ms)':<10}")
    print(f"  {'─'*60}")

    for level in levels:
        results = asyncio.run(_stress_wave(level))
        successes = [r for r in results if r["status_code"] == 200]
        failures  = [r for r in results if r["status_code"] != 200]
        lats      = [r["latency_ms"] for r in results]
        mean_lat  = statistics.mean(lats) if lats else 0

        status_icon = GREEN + "✔" + RESET if not failures else (
            YELLOW + "⚠" + RESET if len(failures) < level // 2 else RED + "✘" + RESET
        )
        print(f"  {level:<8} {status_icon} {len(successes):<7} {len(failures):<6} "
              f"{mean_lat:<12.0f} {max(lats):<10.0f} {min(lats):<10.0f}")

    print()
    info("Interpretation:")
    info("  — Mean latency growing linearly with users = normal queue behind Ollama")
    info("  — Failures appearing = backend/Ollama saturated; consider a larger model server")


# ══════════════════════════════════════════════════════════════════════════════
# 3. FAILURE HANDLING
# ══════════════════════════════════════════════════════════════════════════════
def run_failure_tests():
    """
    Verify the API handles bad inputs gracefully (no 500 crashes).

    Each sub-test sends an intentionally bad request and checks that
    the server returns the expected HTTP error code.
    """
    header("3 · FAILURE HANDLING")
    info(f"Target: {CHAT_ENDPOINT}\n")

    results = []  # (test_name, passed: bool, detail: str)

    # ── Helper ────────────────────────────────────────────────────────────────
    def check(name: str, payload: dict,
              expected_status: int, note: str = ""):
        try:
            resp = requests.post(CHAT_ENDPOINT, json=payload, timeout=15)
            passed = resp.status_code == expected_status
            detail = f"HTTP {resp.status_code} (expected {expected_status})"
            if not passed:
                detail += f" | body: {resp.text[:120]}"
            results.append((name, passed, detail))
            (ok if passed else fail)(f"{name:<45} {detail}")
        except requests.ConnectionError as e:
            results.append((name, False, f"Connection error: {e}"))
            fail(f"{name:<45} Connection error")

    def check_http(name: str, method: str, url: str,
                   expected_status: int, **kwargs):
        try:
            resp = getattr(requests, method)(url, timeout=10, **kwargs)
            passed = resp.status_code == expected_status
            detail = f"HTTP {resp.status_code} (expected {expected_status})"
            if not passed:
                detail += f" | body: {resp.text[:120]}"
            results.append((name, passed, detail))
            (ok if passed else fail)(f"{name:<45} {detail}")
        except requests.ConnectionError as e:
            results.append((name, False, f"Connection error: {e}"))
            fail(f"{name:<45} Connection error")

    # ── Test 1: Empty message ─────────────────────────────────────────────────
    check(
        "Empty message string",
        {"session_id": "fail-test-1", "message": ""},
        expected_status=422,   # FastAPI/Pydantic rejects min_length=1
    )

    # ── Test 2: Whitespace-only message ───────────────────────────────────────
    check(
        "Whitespace-only message",
        {"session_id": "fail-test-2", "message": "   "},
        expected_status=400,   # Backend custom validation
    )

    # ── Test 3: Missing 'message' field ───────────────────────────────────────
    check(
        "Missing 'message' field",
        {"session_id": "fail-test-3"},
        expected_status=422,
    )

    # ── Test 4: Missing 'session_id' field ────────────────────────────────────
    check(
        "Missing 'session_id' field",
        {"message": "Hello"},
        expected_status=422,
    )

    # ── Test 5: Empty session_id ──────────────────────────────────────────────
    check(
        "Empty session_id",
        {"session_id": "", "message": "Hello"},
        expected_status=422,   # Field(...) min_length enforced by FastAPI
    )

    # ── Test 6: Very long message (>10 000 chars) ─────────────────────────────
    check(
        "Oversized message (10 001 chars)",
        {"session_id": "fail-test-6", "message": "A" * 10_001},
        expected_status=200,   # API should handle it (LLM may truncate)
    )

    # ── Test 7: SQL injection attempt ─────────────────────────────────────────
    check(
        "SQL injection in message",
        {"session_id": "fail-test-7",
         "message": "' OR '1'='1'; DROP TABLE sessions; --"},
        expected_status=200,   # Must NOT 500 — treated as plain text by LLM
    )

    # ── Test 8: JSON injection in session_id ─────────────────────────────────
    check(
        "JSON injection in session_id",
        {"session_id": '{"$ne": null}', "message": "test"},
        expected_status=200,   # Stored as plain string key, not executed
    )

    # ── Test 9: Non-existent REST route ───────────────────────────────────────
    check_http(
        "GET on non-existent route",
        "get", f"{BASE_URL}/api/nonexistent",
        expected_status=404,
    )

    # ── Test 10: Health endpoint ──────────────────────────────────────────────
    check_http(
        "GET /health returns 200",
        "get", HEALTH_URL,
        expected_status=200,
    )

    # ── Test 11: Wrong HTTP method on /api/chat ───────────────────────────────
    check_http(
        "GET /api/chat (wrong method)",
        "get", CHAT_ENDPOINT,
        expected_status=405,
    )

    # ── Test 12: Malformed JSON body ──────────────────────────────────────────
    try:
        resp = requests.post(
            CHAT_ENDPOINT,
            data="not json at all!!!",
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        passed = resp.status_code == 422
        detail = f"HTTP {resp.status_code} (expected 422)"
        results.append(("Malformed JSON body", passed, detail))
        (ok if passed else fail)(f"{'Malformed JSON body':<45} {detail}")
    except requests.ConnectionError as e:
        fail(f"{'Malformed JSON body':<45} Connection error: {e}")
        results.append(("Malformed JSON body", False, str(e)))

    # ── Summary ───────────────────────────────────────────────────────────────
    passed  = sum(1 for _, p, _ in results if p)
    total   = len(results)
    print(f"\n  Result: {passed}/{total} failure-handling tests passed.")
    if passed == total:
        ok("All failure-handling checks passed — API is robust.")
    else:
        warn(f"{total - passed} check(s) did not return the expected status code.")
        info("This may indicate missing input validation or unhandled edge cases.")


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="Hotel AI benchmark & failure test suite"
    )
    parser.add_argument("--latency",  action="store_true",
                        help="Run latency benchmark only")
    parser.add_argument("--stress",   action="store_true",
                        help="Run stress test only")
    parser.add_argument("--failure",  action="store_true",
                        help="Run failure-handling tests only")
    parser.add_argument("--requests", type=int, default=5,
                        help="Number of requests for latency benchmark (default 5)")
    parser.add_argument("--max-users", type=int, default=10,
                        help="Max concurrent users for stress test (default 10)")
    parser.add_argument("--step",     type=int, default=2,
                        help="Concurrency ramp step for stress test (default 2)")
    args = parser.parse_args()

    run_all = not (args.latency or args.stress or args.failure)

    if args.latency or run_all:
        run_latency_benchmark(num_requests=args.requests)

    if args.stress or run_all:
        run_stress_test(max_users=args.max_users, step=args.step)

    if args.failure or run_all:
        run_failure_tests()

    print(f"\n{BOLD}Done.{RESET}\n")


if __name__ == "__main__":
    main()
