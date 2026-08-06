# Runbook: API Not Ready / Database Dependency Failure

## 1. Purpose
This runbook guides an operator through the triage, investigation, recovery, and escalation of an incident where the FastAPI service is running but its PostgreSQL database dependency is unavailable, causing the service readiness check (`/ready`) to fail.

---

## 2. Ownership
*   **Primary Owner (First Responder)**: Service/API Operator (Triage, logs inspection, restart check)
*   **Dependency Owner**: Database/Infrastructure Team (PostgreSQL logs, volume diagnostics)
*   **Escalation Path**: On-Call Lead / Engineering Owner (If database fails to start or data corruption is suspected)

---

## 3. Alert
*   **Triggering Alert**: `APIUnavailable`
*   **Expression**: `application_ready == 0` for `15s`
*   **Alert Context**: The alert fires when the database connection checks in the API fail continuously. This means the FastAPI application is alive but cannot serve traffic because it cannot query PostgreSQL.
*   **Key Distinction**: Process liveness (`/health` returning `200`) does **not** mean the service is ready (`/ready` returning `503`). Do not kill the API process if `/health` is healthy.

---

## 4. Symptoms
*   API responses to client operations fail or return empty/degraded states.
*   Availability Alert `APIUnavailable` state is `FIRING` in Prometheus.
*   HTTP readiness endpoint `/ready` returns `HTTP 503 Service Unavailable`.
*   FastAPI application logs display PostgreSQL connection exceptions.

---

## 5. Initial Triage
Begin immediately with the following commands to confirm the outage state:

1.  **Check API process liveness**:
    ```bash
    curl -i http://localhost:8000/health
    ```
    *   *Interpretation*: `200 OK` indicates the FastAPI process is alive.

2.  **Check API readiness**:
    ```bash
    curl -i http://localhost:8000/ready
    ```
    *   *Interpretation*: `503 Service Unavailable` confirms a dependency connectivity outage.

3.  **Check Docker Compose service status**:
    ```bash
    docker compose ps
    ```
    *   *Interpretation*: Verify if the `fastapi-book-db` service is `Up` or `Stopped`.

4.  **Inspect recent logs**:
    ```bash
    docker compose logs --tail=50 api
    docker compose logs --tail=50 db
    ```
    *   *Interpretation*: Look for connection socket timeouts or PostgreSQL shutdown logs.

---

## 6. Investigation Decision Tree

```text
               [ APIUnavailable Alert Firing ]
                              │
                              ▼
                Is /health returning 200 OK?
                              │
                 ┌────────────┴────────────┐
                 No                        Yes
                 │                          │
                 ▼                          ▼
         Investigate API              Is /ready returning 200 OK?
         crashed container                  │
                               ┌────────────┴────────────┐
                               No                        Yes
                               │                          │
                               ▼                          ▼
                     Check DB container status      Investigate traffic,
                     & credentials/socket binds     networking, or latency.
```

---

## 7. Recovery (Targeted)
If the database service container is confirmed stopped or unhealthy, recover it manually:

```bash
docker compose start db
```

> [!WARNING]
> *   **Do NOT restart the entire stack** (`docker compose down && docker compose up -d`) as your first action. Doing so destroys active logs, kills active API client sessions, and increases downtime.
> *   **CRITICAL CAUTION**: Never run `docker compose down -v`. The `-v` flag deletes the persistent named volume containing all database tables and seed records, resulting in permanent data loss.

---

## 8. Validation Criteria
The incident is considered fully resolved **only** when all of the following conditions are true:
*   [ ] **Database Healthy**: `docker compose ps` shows `fastapi-book-db` status as `Up (healthy)`.
*   [ ] **PostgreSQL Ready**: DB logs show `database system is ready to accept connections`.
*   [ ] **Liveness verified**: `curl -i http://localhost:8000/health` returns `HTTP 200`.
*   [ ] **Readiness verified**: `curl -i http://localhost:8000/ready` returns `HTTP 200` (`{"status":"ready"}`).
*   [ ] **Functional verification**: Creating a record succeeds:
    ```bash
    curl -i -X POST -H "Content-Type: application/json" -d '{"id": 4, "title": "The Silmarillion", "author": "J.R.R. Tolkien", "publication_year": 1977, "genre": "Fantasy"}' http://localhost:8000/api/v1/books/
    ```
    (Expect `HTTP 201 Created` and returned book details).
*   [ ] **Data Persistence verified**: Querying `curl http://localhost:8000/api/v1/books/` returns all pre-existing books (IDs 1, 2, and 3).
*   [ ] **Prometheus Scraping target**: `http://localhost:9090/targets` shows target `fastapi-app` state as `UP`.
*   [ ] **Alert state cleared**: `http://localhost:9090/alerts` shows `APIUnavailable` alert cleared back to `INACTIVE`.

---

## 9. Rollback Guidance
*   **Dependency Recovery**: Re-run database container startup commands.
*   **Application Rollback**: Only consider rolling back the API version if the outage was immediately preceded by an API code deployment.
*   *Note*: Application rollback is outside the scope of this local Compose environment. If investigation identifies a recent application change as the cause, revert that change through normal version control and redeploy, rather than modifying containers manually.

---

## 10. Escalation Guidance
Stop attempting local recovery and escalate immediately to the Database Team or Engineering Owner if:
1.  The database container fails to start, repeatedly crashes, or prints database startup corruption logs.
2.  `/ready` remains `503` despite the database report showing it is accepting connections.
3.  Pre-existing database data is missing or corrupted.
4.  Destructive operations (e.g. database schema modifications or volume reformats) are required to restore service.

**Information to gather before escalation**:
*   Active Alert name and firing timestamp.
*   Current liveness and readiness status responses.
*   Logs snippet of the last 50 lines from `api` and `db`.
*   Target status from Prometheus rules.
*   List of recovery commands already executed.

---

## 11. Failure Simulation
To safely reproduce the incident locally for testing or training:
1.  Run the reproducible simulation script:
    ```bash
    ./scripts/simulate-db-failure.sh
    ```
2.  Observe the terminal output confirming `/ready → 503` and alert state transition.
3.  Do not automate remediation. Recover manually using `docker compose start db` to verify the runbook loop.

---

## 12. Root Cause Summary
*   **Root Cause**: The PostgreSQL database container was stopped during a controlled SRE failure simulation.
*   **Impact**: The FastAPI process remained running, but the application could not satisfy its database dependency, causing the readiness check `/ready` to return `503 Service Unavailable`.
*   **Detection**: readiness signal degradation and the `APIUnavailable` alert firing.
*   **Recovery**: The stopped database container was restarted.
*   **Validation**: Readiness returned to `200`, data persistence was verified, and the Prometheus alert cleared.

---

## 13. Evidence

| Stage | Expected Status | Actual Result | Timing |
| :--- | :--- | :--- | :--- |
| **Baseline (Healthy)** | `/health: 200`, `/ready: 200` | Healthy, serving data | `01:28:36 UTC` |
| **Failure Injected** | DB stopped, `/ready: 503` | Verified stopped, readiness drops | `01:28:54 UTC` |
| **Alert Firing** | `APIUnavailable` state: firing | Fired in Prometheus | `01:29:12 UTC` |
| **Recovery command** | `docker compose start db` | Started container | `02:05:06 UTC` |
| **Readiness Restored** | `/ready: 200` | Reconnected automatically | `02:05:18 UTC` |
| **Validation** | Book create succeeds, data intact | Confirmed write/read | `02:05:38 UTC` |
| **Alert Cleared** | `APIUnavailable` state: inactive | Cleared back to inactive | `02:05:37 UTC` |

*   **Time to Detection**: ~18.5 seconds
*   **Time to Recovery**: ~12.0 seconds
*   **Alert Clearance Time**: ~31.0 seconds

---

## 14. Cost Considerations
*   **Current Setup**: The local environment runs purely within Docker Compose (`api`, `db`, `prometheus` containers) and has zero cloud infrastructure billing costs.
*   **Production Scaling**: When promoting this design to production, SREs must bound operational overhead:
    *   **Prometheus retention**: Bounded storage retention (e.g. 15 days) and metric scrape intervals (e.g. 15 seconds) to avoid disk exhaustion.
    *   **Logs volume**: Bounded logs size through rotation and log level tuning (suppressing high-frequency `/health` and `/ready` request entries in standard middleware logs).

---

## 15. Preventive Improvement
*   **Selected Improvement**: **Database Connection Resiliency / Automatic Retries with Exponential Backoff**
*   **Observed Weakness**: Currently, if the database starts slightly slower than the API during container restarts or network shifts, or has a transient disconnect, the database instantiation checks inside `api/db/schemas.py` fail immediately, leading to connection exceptions that require manual operator awareness or API container restarts if the system fails to auto-reconnect cleanly.
*   **Benefits**: Automatically absorbs transient database restarts and networking drops. If the database drops out for 5 seconds, the connection pool will silently retry with backoff, preventing readiness signals from immediately failing and page alerts from triggering unnecessarily.
*   **Trade-off/Cost**: Slightly increases endpoint response latency during active retries before connection exhaustion occurs.
