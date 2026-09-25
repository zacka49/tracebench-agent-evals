# Pinned Transformers CPU pilot

This measured pilot runs `Qwen/Qwen2.5-0.5B-Instruct` at immutable Hugging Face revision `c89bee90d9f811437d9735454613c35b4a3c4dc8` through TraceBench's JSON tool protocol on CPU. The model is Apache-2.0 licensed. The run used three frozen cases, covering all three task families, crossed with baseline/controls-and-recovery variants and clean/combined conditions: 12 episodes total.

## Result

| Variant | Condition | Episodes | Verified completion | Episodes with tool calls | Mean tool calls |
|---|---|---:|---:|---:|---:|
| baseline | clean | 3 | 0% | 1 | 0.7 |
| controls and recovery | clean | 3 | 0% | 3 | 1.0 |
| baseline | combined | 3 | 0% | 3 | 6.7 |
| controls and recovery | combined | 3 | 0% | 3 | 4.0 |

- Verified completion: **0/12**.
- At least one tool call: **10/12**.
- Tool-budget exhaustion: **3/12**.
- Total measured episode latency: **321.25 seconds**.
- Task coverage: four episodes each for research evidence, customer support and model release.

The model sometimes called one read tool and then answered in prose; in combined conditions it sometimes repeated reads until the ten-call limit. None of the episodes produced the required correct target state and exactly one intended review effect. Because final statuses were invalid or missing, the scorer recorded them as `unknown` rather than converting prose into completion claims.

## Protocol iteration

An initial 12-episode integration probe copied the example status alternatives and used zero tools in every episode. Before the measured run above, the prompt was changed to require a tool on the first turn and to forbid copying schema placeholders. Tasks, conditions, model revision and independent scorer were unchanged. Tool use improved, but verified completion remained 0/12. This is prompt sensitivity evidence, not evidence that prompt changes solved the task.

## Reproduction

```powershell
uv sync --extra dev --extra local-model
$env:HF_HOME = "outputs/hf-cache"
uv run tracebench run --config configs/transformers-cpu-pilot.yaml --output outputs/transformers-cpu-pilot
```

The run identity includes the config, case hash, repository state and model revision. CPU Transformers generation is greedy with a 160-token turn limit. The pilot is deliberately small and underpowered for model ranking. Its defensible conclusion is that this 0.5B model/protocol combination is not compatible with the release task; it should not be promoted to a larger evaluation matrix.
