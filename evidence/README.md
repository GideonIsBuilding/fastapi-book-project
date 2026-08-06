# Operational Readiness Evidence

This directory contains evidence from a controlled PostgreSQL failure simulation performed against the local test environment.

The evidence demonstrates:

1. Healthy baseline
2. Failure detection
3. Investigation
4. Recovery
5. Post-recovery validation

All testing was performed locally using synthetic data.

## Evidence sequence

| File | Purpose |
|------|---------|
| [baseline.md](baseline.md) | Healthy state before failure |
| [failure.md](failure.md) | Failure injection and detection |
| [timeline.md](timeline.md) | Chronological incident sequence |
| [recovery.md](recovery.md) | Recovery and post-recovery validation |

## Reproduction

The failure can be reproduced using:

`scripts/simulate-db-failure.sh`

## Case Study 3 Evidence Mapping

| Requirement | Evidence |
|-------------|----------|
| Early detection | Grafana readiness + alert state |
| Investigation | Readiness, dependency, error and latency signals |
| Recovery | PostgreSQL restoration + readiness recovery |
| Validation | Successful readiness/API checks |
| Reproducibility | Failure simulation script |
