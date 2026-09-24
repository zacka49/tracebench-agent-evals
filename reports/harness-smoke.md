# Harness smoke run

This checked-in report records the deterministic 64-episode harness run from
`configs/smoke.yaml`. The scripted provider is a test control, not a model result.

| Variant | Condition | Episodes | Verified completion | False completion | Fault recovery | Duplicate effects |
|---|---|---:|---:|---:|---:|---:|
| baseline | clean | 8 | 100% | 0% | 0% | 0 |
| baseline | fault | 8 | 0% | 100% | 0% | 8 |
| baseline | misleading | 8 | 0% | 100% | 0% | 0 |
| baseline | combined | 8 | 0% | 100% | 0% | 8 |
| controls_and_recovery | clean | 8 | 100% | 0% | 0% | 0 |
| controls_and_recovery | fault | 8 | 100% | 0% | 100% | 0 |
| controls_and_recovery | misleading | 8 | 100% | 0% | 0% | 0 |
| controls_and_recovery | combined | 8 | 100% | 0% | 100% | 0 |

The paired verified-completion difference on fault and combined conditions was
**+100 percentage points** (task-cluster bootstrap interval: +100 to +100). The
zero-width interval is expected because every synthetic case has the same designed
outcome. It proves the fault injector, recovery path and scorer agree on the fixture; it
does not estimate performance on unseen tasks.

The baseline duplicates review requests after post-commit timeouts because it retries
the mutation without reconciling state. The recovery control reads the review list after
the ambiguous response and avoids a second write. Misleading conditions instead test
whether the agent uses approved provenance rather than a higher stale value.

