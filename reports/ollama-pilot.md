# Ollama pilot: qwen3:0.6b

This is a deliberately small local-model integration pilot: two task cases, two agent
variants and two conditions, for eight episodes in total. It verifies that TraceBench can
run a real native tool-calling model and preserve unsuccessful episodes.

| Variant | Condition | Episodes | Verified completion | False completion | Mean tool calls |
|---|---|---:|---:|---:|---:|
| baseline | clean | 2 | 0% | 100% | 4.0 |
| baseline | combined | 2 | 0% | 100% | 4.0 |
| controls_and_recovery | clean | 2 | 0% | 100% | 5.0 |
| controls_and_recovery | combined | 2 | 0% | 100% | 5.0 |

The model often created the review request while skipping or malformed the required
report update. Because the scorer checks the final world state, a confident final message
does not turn that partial execution into a pass. This pilot is failure evidence and an
end-to-end adapter check, not a model comparison.

## Run identity

- Model: `qwen3:0.6b`
- Ollama digest: `7df6b6e09427a769808717c0a93cadc4ae99ed4eb8bf5ca557c90846becea435`
- Format and quantisation: GGUF, Q4_K_M
- Parameter size reported by Ollama: 751.63M
- Decoding: temperature 0, seed 17
- Configuration: `configs/ollama-pilot.yaml`

The sample is too small for a capability claim. A useful follow-up would freeze several
larger tool-capable models, increase the task count, repeat each cell, and report paired
task-level intervals plus cost and latency.

