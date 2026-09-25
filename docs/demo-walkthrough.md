# TraceBench: three-minute walkthrough

## Audience and decision

TraceBench answers a release question: does an agent actually complete a bounded tool task safely when evidence is stale or a write response is ambiguous? It scores world state and events instead of trusting the final message.

## Before the recording

```powershell
uv sync --extra dev
uv run pytest -q
uv run tracebench run --config configs/smoke.yaml --output outputs/smoke
Start-Process outputs/smoke/report.html
```

## Recording script

**0:00–0:35 — Show the failure mode.** Use the README visual to explain how a post-commit timeout can make a retry create duplicate work, even when the final answer sounds confident.

**0:35–1:15 — Compare variants.** Open the smoke report and compare baseline, prompt-only, controls-only and controls-with-recovery on identical tasks and conditions. Explain that the scripted provider is a harness control rather than model evidence.

**1:15–1:55 — Inspect one trace.** Open an episode with the combined condition. Follow the action, injected ambiguity, append-only event and independent final-state score. Point out the distinction between attempted and executed violations.

**1:55–2:30 — Show model evidence.** Open the model-backed pilot report. Explain the immutable model revision, task-family coverage and any failure honestly. A zero-pass result still demonstrates that protocol compliance and tool use are measured rather than assumed.

**2:30–3:00 — Explain the release decision.** State what the sample can and cannot establish, how a larger paired matrix would be budgeted, and why unsafe effects, harness errors and model refusals remain separate outcomes.

## Interview prompts this supports

- Why is final-answer accuracy insufficient for agents?
- How do idempotency and reconciliation differ?
- What is the independent unit for uncertainty?
- How would you prevent the evaluator from trusting the system under test?
