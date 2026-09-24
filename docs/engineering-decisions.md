# Engineering decisions

## Score world state independently

The scorer reads the final report, reviews and append-only events. This prevents fluent
self-reports from hiding partial work and lets the benchmark distinguish attempted policy
violations from actions that actually executed.

## Inject post-commit failures

A timeout before mutation is easy to retry. A timeout after commit forces the agent to
reconcile state before deciding whether another write is safe, which is the failure mode
the benchmark is intended to expose.

## Keep a no-model control path

The deterministic provider makes CI fast and proves the interventions and metrics work.
Model-backed results are labelled separately so test fixtures cannot be presented as model
improvements.

## Store failed episodes

Adapter and runtime errors stay in the denominator with status and error fields. Dropping
them would bias reported success upward and make infrastructure regressions hard to debug.

