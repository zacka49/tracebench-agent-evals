# v0.2 native tool-call compatibility gate

Run date: 24 September 2026. These are deliberately small integration checks, not model
rankings. They test whether an Ollama model follows TraceBench's native tool protocol and
whether the resulting workspace passes the independent state-based scorer.

| Model | Ollama digest | Episodes | Verified completion | False completion | Mean tool calls |
|---|---|---:|---:|---:|---:|
| qwen3:0.6b | `7df6b6e09427a769808717c0a93cadc4ae99ed4eb8bf5ca557c90846becea435` | 8 | 0% | 100% | 0.0 |
| qwen3:4b-instruct | `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0` | 1 | 100% | 0% | 6.0 |

The 0.6B run covered two cases, the baseline and controls-and-recovery variants, and clean
and combined conditions. Every episode returned a completed claim without calling a tool.
The harness retained all eight failures and classified them as false completion. Strengthening
the prompt to require observed tool state did not make this model compatible.

The 4B gate used one baseline/clean case. It made six tool calls and produced the exact
approved metric, provenance, and single idempotent review request required by the scorer.
This shows that the adapter and protocol work with at least one pinned local model. It does
not establish a general 4B capability rate; a proper comparison needs more cases, repeated
seeds, paired conditions, and uncertainty intervals.

Reproduce with:

```powershell
uv run tracebench run --config configs/ollama-compat.yaml --output outputs/compat-06b
uv run tracebench run --config configs/ollama-compat-4b.yaml --output outputs/compat-4b
```

The earlier qwen3:0.6b pilot used a prior prompt/protocol and did make tool calls, although
none of its episodes passed. That difference is evidence of prompt and protocol sensitivity,
so results should always record the repository revision alongside the model digest.
