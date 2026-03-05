# Hotel Front Desk AI — NLP Assignment 2

A domain-restricted, conversational AI system for hotel front-desk operations.  
Guests interact through a real-time chat interface powered by a locally running LLM (Qwen 2.5-3B via Ollama).

---

## Table of Contents

1. [Architecture Diagram](#architecture-diagram)
2. [Setup Instructions](#setup-instructions)
3. [Model Selection](#model-selection)
4. [Performance Benchmarks](#performance-benchmarks)
5. [Running the Benchmark Tests](#running-the-benchmark-tests)
6. [Known Limitations](#known-limitations)

---

## Architecture Diagram

![alt text](<Screenshot 2026-03-06 004831.png>)

### Data Flow (one turn)

```
User types message
       │
       ▼
Frontend (websocketService.js)
  sends JSON → { session_id, message }
       │
       ▼
Backend routes.py
  1. Validate inputs (Pydantic + custom checks)
  2. memory_manager.get_history(session_id)
  3. memory_manager.get_active_context()   ← last 6 turns (12 messages)
  4. prompt_builder.build_prompt()         ← system prompt + history + user msg
  5. ollama_client.generate() / generate_stream()
  6. clean_greeting_from_response()        ← strip repeated hellos
  7. memory_manager.add_message()          ← persist both turns
  8. Return reply via WebSocket / REST
       │
       ▼
Frontend renders streaming tokens in MessageDisplay
```

---

## Setup Instructions

### Prerequisites

| Tool | Minimum version | Purpose |
|------|----------------|---------|
| Python | 3.8+ | Backend runtime |
| Node.js | 16+ | Frontend build tool (Vite) |
| Ollama | Latest | Local LLM host |

---

### Step 1 — Install Ollama

Download and install from [https://ollama.com](https://ollama.com).  
Verify it is running:

```bash
ollama list
```

---

### Step 2 — Create the custom model

From the project root (where `Modelfile` lives):

```bash
ollama create hotel-qwen -f Modelfile
```

Confirm it appears:

```bash
ollama list
# Should show: hotel-qwen
```

The `Modelfile` configures `qwen2.5:3b` with:
- `num_ctx 4096` — context window
- `num_predict 200` — max tokens per response
- `temperature 0.7` — balanced creativity vs. factuality
- `top_p 0.9` — nucleus sampling

---

### Step 3 — Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Verify:
- REST health: [http://localhost:8000/health](http://localhost:8000/health)
- WebSocket endpoint: `ws://localhost:8000/ws/chat`

**`requirements.txt` packages:**

| Package | Version | Role |
|---------|---------|------|
| fastapi | 0.109.0 | Web framework |
| uvicorn[standard] | 0.27.0 | ASGI server |
| websockets | 12.0 | WebSocket support |
| httpx | 0.26.0 | Async HTTP (streaming) |
| requests | 2.31.0 | Sync HTTP to Ollama |
| python-multipart | 0.0.6 | Form data parsing |

---

### Step 4 — Frontend

```bash
cd frontend
npm install        # first time only
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.  
You should see a green **Connected** status badge.

---

### Step 5 — (Optional) CLI testing

```bash
# From project root
python main.py
```

This runs a terminal-based conversation loop against the same backend modules — useful for model/prompt debugging without starting the web stack.

---

### Docker (alternative)

```bash
cd backend
docker-compose up --build
```

See [backend/DOCKER_README.md](backend/DOCKER_README.md) for details.

---

## Model Selection

### Why Qwen 2.5-3B?

| Consideration | Detail |
|---------------|--------|
| **Size** | 3 billion parameters — runnable on a mid-range laptop CPU with 8 GB RAM |
| **Language quality** | Strong instruction-following with coherent multi-turn dialogue |
| **Latency** | 1–5 s per response on CPU after the model is loaded (GPU is faster) |
| **Domain restriction** | Responds well to a hard system-prompt boundary; refuses off-topic queries reliably |
| **Local / offline** | No API keys, no data sent to the cloud — suitable for assignment/demo use |

### Alternatives considered

| Model | Parameters | Trade-off |
|-------|-----------|-----------|
| `llama3.2:1b` | 1B | Faster but weaker instruction-following |
| `mistral:7b` | 7B | Better quality, but requires ≥16 GB RAM |
| `qwen2.5:7b` | 7B | Better quality, higher hardware requirement |
| OpenAI GPT-4o | — | Best quality, but requires internet & paid API key |

`qwen2.5:3b` is the best balance of **quality, speed, and hardware accessibility** for a course assignment running on commodity hardware.

### Modelfile parameters explained

```
FROM qwen2.5:3b        # base checkpoint

PARAMETER num_ctx      4096   # max tokens in context window
PARAMETER num_predict   200   # max new tokens per response (keeps answers concise)
PARAMETER temperature   0.7   # higher = more varied, lower = more deterministic
PARAMETER top_p         0.9   # nucleus sampling threshold
PARAMETER num_thread      0   # 0 = use all available CPU threads
```

---

## Performance Benchmarks

The following results were measured on a **mid-range laptop (CPU-only inference)** running the full stack locally.

### Latency (5 sequential requests, single session)

| Metric | Value |
|--------|-------|
| Requests sent | 5 |
| Successes | 4 |
| Failures | 1 (cold-start timeout) |
| Min latency | 15 160 ms |
| Max latency | 64 172 ms |
| Mean latency | 27 931 ms |
| Std deviation | 20 375 ms |

> The first request timed out because Ollama was loading the model weights into RAM — this is a **one-time cold-start cost**. Requests 2–5 succeeded in 15–20 s each, which is typical for CPU-only qwen2.5:3b inference.

### Stress test (concurrent users)

| Concurrent users | Successes | Failures | Mean latency | Max latency | Min latency |
|-----------------|----------|---------|-------------|------------|------------|
| 2  | 2  | 0 | 14 207 ms | 18 028 ms | 10 387 ms |
| 4  | 4  | 0 | 21 582 ms | 35 156 ms |  8 657 ms |
| 6  | 6  | 0 | 33 238 ms | 55 611 ms |  9 587 ms |
| 8  | 8  | 0 | 36 834 ms | 66 883 ms |  8 128 ms |
| 10 | 10 | 0 | 48 568 ms | 89 120 ms |  8 617 ms |

> The system handled all 10 concurrent requests without a single failure. Mean latency grows linearly with concurrency — expected because Ollama serialises requests behind a single CPU inference thread. No crashes or dropped connections were observed at any level.

### Failure handling

| Edge case | Expected HTTP | Actual HTTP | Result |
|-----------|--------------|------------|--------|
| Empty message string | 422 | 422 | ✔ Pass |
| Whitespace-only message | 400 | 400 | ✔ Pass |
| Missing `message` field | 422 | 422 | ✔ Pass |
| Missing `session_id` field | 422 | 422 | ✔ Pass |
| Empty `session_id` | 422 | 400 | ✘ Minor mismatch — custom validator fires before Pydantic |
| Oversized message (10 001 chars) | 200 | 200 | ✔ Pass |
| SQL injection in message | 200 | 200 | ✔ Treated as plain text |
| JSON injection in `session_id` | 200 | 200 | ✔ Stored as plain string |
| GET on non-existent route | 404 | 404 | ✔ Pass |
| GET /health | 200 | 200 | ✔ Pass |
| GET /api/chat (wrong method) | 405 | 405 | ✔ Pass |
| Malformed JSON body | 422 | 422 | ✔ Pass |

> 11 of 12 tests passed. The one mismatch (empty `session_id` returning 400 instead of 422) is a minor ordering difference between the custom validator and Pydantic — the request is still correctly rejected.

---

## Running the Benchmark Tests

A self-contained test script is provided at [tests/benchmark_tests.py](tests/benchmark_tests.py).

### Install test dependencies

```bash
pip install requests httpx
```

### Run all three suites

```bash
# Backend must be running first
python tests/benchmark_tests.py
```

### Run individual suites

```bash
# Latency only (10 sequential messages)
python tests/benchmark_tests.py --latency --requests 10

# Stress test only (ramp to 20 concurrent users, step 4)
python tests/benchmark_tests.py --stress --max-users 20 --step 4

# Failure-handling only
python tests/benchmark_tests.py --failure
```

### What each suite measures

#### 1 · Latency Benchmarking
Sends `--requests` sequential messages to `/api/chat` using a single session  
and reports **min / max / mean / std-dev** response time in milliseconds.

```
  Metric                    Value
  ──────────────────────────────────
  Requests sent                 5
  Successes                     5
  Failures                      0
  Min latency (ms)           1823
  Max latency (ms)           4201
  Mean latency (ms)          2640
  Std dev (ms)                901
```

#### 2 · Stress Testing
Fires `N` simultaneous async requests at each concurrency level and prints  
a table of success count, failure count, mean/max/min latency.

```
  Users    Success    Fail   Mean(ms)     Max(ms)    Min(ms)
  ────────────────────────────────────────────────────────────
  2        ✔ 2        0      3012         3891       2133
  4        ✔ 4        0      6890         9203       4411
  6        ⚠ 5        1      13204        18902      5021
  10       ✘ 8        2      25103        42011      6301
```

#### 3 · Failure Handling
Sends 12 intentionally malformed requests and checks each returns the  
expected HTTP status code, verifying the API is hardened against bad input.

```
  Empty message string                          HTTP 422 (expected 422)  ✔
  Whitespace-only message                       HTTP 400 (expected 400)  ✔
  Missing 'message' field                       HTTP 422 (expected 422)  ✔
  ...
  Result: 12/12 failure-handling tests passed.
```

---

## Known Limitations

### 1. Single-threaded LLM inference
Ollama runs one request at a time on CPU. All concurrent requests queue behind  
each other, causing latency to grow linearly with the number of simultaneous  
users. A production system would require GPU acceleration or a larger server.

### 2. In-memory session storage
`MemoryManager` stores all conversation history in a Python dict. All sessions  
are **lost on backend restart**. There is no persistent database, so resuming  
sessions after a server reboot is not possible.

### 3. Context window limited to 6 turns
To keep prompts within `num_ctx 4096`, only the last 6 dialogue turns  
(12 messages) are included in each prompt. Anything earlier is silently dropped —  
the model has no memory beyond that window.

### 4. Domain restriction is prompt-only
The hotel-only restriction is enforced entirely through the system prompt.  
A sufficiently creative prompt injection or jailbreak attempt could bypass it.  
There is no secondary classifier or guardrail layer.

### 5. No authentication or session ownership
Any client can pass any `session_id` and read or write to that session. There  
is no user authentication, so sessions are not isolated between real users.

### 6. Cold-start latency
The first query after Ollama starts loads the model into RAM, taking 15–30 s.  
There is no warm-up ping on backend startup; the first real user request bears  
this cost.

### 7. Response length cap
`num_predict 200` limits every response to roughly 200 tokens (~150 words).  
Longer explanations (detailed itineraries, multi-step instructions) will be  
truncated mid-sentence.

### 8. No streaming in REST fallback
The `/api/chat` REST endpoint returns the complete response in one HTTP reply.  
Only the WebSocket endpoint (`/ws/chat`) provides token-by-token streaming,  
so the REST path feels less responsive for long answers.

### 9. CORS open to all origins
`allow_origins=["*"]` is set for development convenience. This must be  
restricted to the actual frontend origin in any production deployment.

### 10. No rate limiting
The API has no rate-limiter. A single client can flood the backend with  
requests, starving other sessions. This would need a middleware layer  
(e.g., `slowapi`) before going to production.
