# TraceBench multi-family harness smoke v3

Run on 25 September 2026 with the scripted control:

```powershell
uv run tracebench run --config configs/smoke.yaml --output outputs/smoke-v3 --no-resume
```

The run completed 64/64 episodes: eight cases, two variants and four conditions. The cases covered `research_evidence` (24 episodes), `customer_support` (24), and `model_release` (16).

| Variant | Condition | n | Verified completion | False completion | Fault recovery | Duplicate effects |
|---|---|---:|---:|---:|---:|---:|
| baseline | clean | 8 | 100% | 0% | 0% | 0 |
| baseline | misleading | 8 | 0% | 100% | 0% | 0 |
| baseline | fault | 8 | 0% | 100% | 0% | 8 |
| baseline | combined | 8 | 0% | 100% | 0% | 8 |
| controls and recovery | clean | 8 | 100% | 0% | 0% | 0 |
| controls and recovery | misleading | 8 | 100% | 0% | 0% | 0 |
| controls and recovery | fault | 8 | 100% | 0% | 100% | 0 |
| controls and recovery | combined | 8 | 100% | 0% | 100% | 0 |

Controls-and-recovery minus baseline verified completion in fault-bearing conditions was +100 percentage points; the task-cluster bootstrap interval was also +100 to +100 points because the scripted control is designed to exercise the expected mechanism on every case.

This validates the harness, aliases, controls, fault injection and scorer. It is not a language-model result. The three families have distinct task language and tool contracts but share one abstract state-transition structure, so they do not represent three production systems.
