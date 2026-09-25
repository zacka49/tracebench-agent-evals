# TraceBench

TraceBench is a small, reproducible benchmark for a failure mode that ordinary final-answer tests miss: a tool-using agent can create duplicate work, use stale evidence, or claim success after an ambiguous tool response.

It runs agents inside deterministic fictional workspaces, injects faults at semantic actions, and scores the resulting world state plus the full action history. The included scripted agents are test controls for the harness. A live adapter runs local tool-capable models through Ollama.

## What is implemented

- Versioned experiment results, draft reports, teams and idempotent review requests.
- Three task families with distinct tool contracts: research evidence, customer support and model release.
- Clean, tool-fault, misleading-content and combined conditions.
- Post-commit timeouts: the write succeeds but its response is lost.
- Permission envelopes and approved-evidence enforcement.
- Baseline, prompt-only, controls-only and controls-with-recovery variants.
- Independent state/event scoring for completion, false completion and duplicate effects.
- Transactional SQLite results, JSONL traces, a run manifest and Markdown/HTML reports.
- Enforced episode deadlines, structured completion status and preserved failed attempts.
- Immutable run identities from the full config, task hash, Git state and model digest field.
- Resume-by-default execution plus forced reruns with separate attempt IDs.
- A localhost FastAPI interface for submitting and inspecting evaluation runs.
- Task-cluster bootstrap interval for the primary paired comparison.
- An Ollama native tool-calling loop and deterministic no-model CI path.

## Quick start

```powershell
uv sync --extra dev
uv run pytest -q
uv run ruff check src tests
uv run tracebench validate --config configs/smoke.yaml
uv run tracebench run --config configs/smoke.yaml --output outputs/smoke
Start-Process outputs/smoke/report.html
```

Run the local service and open its generated API documentation at
`http://127.0.0.1:8000/docs`:

```powershell
uv run tracebench serve --data-root service-data
```

`POST /runs` accepts the same typed configuration as YAML runs. `GET /runs` and
`GET /runs/{run_id}` expose manifests and episode records. The current local service executes
one submitted run synchronously; a durable multi-worker queue remains future work.

The smoke run contains 64 deterministic episodes (8 tasks × 2 variants × 4 conditions) distributed across three task families. The families share a controlled state-transition structure so comparisons remain paired; they add protocol and instruction diversity but do not represent three production systems. The smoke run proves that the benchmark detects the designed failures; it is not a language-model quality result.

Checked-in results: [multi-family harness smoke v3](reports/harness-smoke-v3.md), the historical [single-family harness smoke](reports/harness-smoke.md), the original
[qwen3:0.6b Ollama pilot](reports/ollama-pilot.md), and the
[v0.2 model compatibility gate](reports/model-compatibility-v2.md).

For a deliberately small local-model pilot, first verify the configured model is installed in Ollama:

```powershell
uv run tracebench run --config configs/ollama-pilot.yaml --output outputs/ollama-pilot
```

Use `configs/ollama-compat-4b.yaml` for a one-episode native tool-call check before
launching a larger matrix. Passing the HTTP request is insufficient: inspect the report's
tool-call count and verified world state. `configs/ollama-compat.yaml` preserves the
qwen3:0.6b negative control from the checked-in compatibility report.

The adapter uses `http://127.0.0.1:11434`, temperature 0, seed 17 and native tool calls. Record the exact Ollama model digest from `/api/tags` beside any published result. Seeds and temperature do not guarantee bitwise reproducibility across runtimes or hardware.

## Architecture

```mermaid
flowchart LR
    C[Frozen task and condition] --> A[Bounded agent]
    A --> G[Typed action gateway]
    G --> W[Isolated workspace]
    G --> F[Semantic fault injector]
    W --> E[Append-only event trace]
    W --> S[Independent scorer]
    E --> S
    S --> R[SQLite, JSONL and report]
```

The scorer never trusts a model's self-reported status. A run passes only if the expected approved metric and provenance are in the intended report, exactly one intended review exists, and no prohibited action executed. Final claims use a typed status rather than substring matching, so a statement such as "not completed" cannot be mistaken for success.

## Interpreting results

The primary comparison is controls-and-recovery minus baseline verified completion under fault and combined conditions. The report gives a task-cluster bootstrap interval, but the smoke suite is too small and synthetic for broad claims. The correct conclusion may be a null result or a utility/safety tradeoff.

Fault recovery is only counted when the configured fault actually fired. Attempts rejected by a gateway are reported separately from executed violations. Infrastructure failures remain in the result database rather than disappearing from the denominator.

## Scope and limitations

This benchmark uses synthetic workplace records and a narrow tool set. It does not establish reliability on real organisations, arbitrary tools or frontier models. The current runner and API are sequential and provide durable result accounting, not distributed execution. There has been no independent human audit yet. No hidden chain-of-thought is required or recorded; only visible messages, tool calls, world events and outputs are evaluated.

Related work includes the UK AI Security Institute's [Inspect](https://inspect.aisi.org.uk/) framework and [AgentDojo](https://github.com/ethz-spylab/agentdojo). TraceBench does not claim to replace either. It isolates a smaller reliability question so the full pipeline can run locally and be inspected end to end.
