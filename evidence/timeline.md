# Incident Timeline: Database Dependency Outage Simulation

This document outlines the chronological timeline of the simulated SRE outage incident and recovery verification.

| Timestamp | SRE Event | Description |
| :--- | :--- | :--- |
| **01:28:36 UTC** | **Baseline Healthy** | Confirmed `/health` → `200`, `/ready` → `200`, Prometheus targets `UP`. |
| **01:28:54 UTC** | **Outage Injected** | Executed `docker compose stop db` to simulate PostgreSQL outage. |
| **01:28:57 UTC** | **Outage Detected** | Metric `application_ready` evaluates to `0.0`. Alert transitions to `PENDING` state. |
| **01:29:12 UTC** | **Alert Fired** | `APIUnavailable` alert status transitions to `FIRING` (15s evaluation time completed). |
| **01:29:26 UTC** | **Triage / Diagnose** | Operator verifies `/health` → `200`, `/ready` → `503`, and logs socket errors. |
| **02:05:06 UTC** | **Recovery Started** | Operator executes `docker compose start db` to restore PostgreSQL. |
| **02:05:10 UTC** | **Database Healthy** | PostgreSQL logs confirm: `database system is ready to accept connections`. |
| **02:05:18 UTC** | **Readiness Restored** | API successfully reconnects. `/ready` returns `HTTP 200 OK`. |
| **02:05:38 UTC** | **Functional Validation** | Created and retrieved Book ID 4. Verified persistence of seed books. |
| **02:05:37 UTC** | **Alert Cleared** | Scrape completes and `APIUnavailable` alert transitions back to `INACTIVE`. |

### Calculations
*   **Time to Detection**: ~18.5 seconds
*   **Time to Recovery**: ~12.0 seconds
*   **Alert Clearance Time**: ~31.0 seconds
