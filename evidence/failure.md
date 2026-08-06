# Failure Detection and Investigation

## Failure Scenario
The PostgreSQL backend database dependency container (`fastapi-book-db`) was stopped. This simulates a clean crash or service drop of the data layer while the FastAPI application container process (`fastapi-book-api`) remains running.

## Failure Injection
The database outage was injected using:
```bash
./scripts/simulate-db-failure.sh
```
This executes `docker compose stop db` locally, leaving data volumes and configurations intact.

## Detection
The system detected the outage using the following observed signals:
*   **Readiness state**: `/ready` dropped immediately to `503 Service Unavailable` returning `{"status":"not_ready","reason":"database_unavailable"}`.
*   **PostgreSQL connectivity**: Database connection status gauge `application_ready` dropped to `0.0`.
*   **Active alert**: Prometheus SRE alert rule `APIUnavailable` transitioned to `firing` after 15 seconds.
*   **HTTP errors**: Database-backed API calls returned connection failures instead of successful data.

## Investigation
The incident investigation followed the operational signals hierarchy:
1.  **Readiness drop**: The readiness check `/ready` began failing with `503` while the liveness probe `/health` continued returning `200 OK`. This immediately pointed to a dependency failure rather than an API process crash.
2.  **Telemetry tracking**: The Prometheus gauge `application_ready == 0` triggered.
3.  **Logs correlation**: Inspection of API logs via `docker compose logs api` revealed database socket exceptions:
    ```text
    Error getting books: Can't create a connection to host db and port 5432
    ```
4.  **Process lookup**: Running `docker compose ps` showed `fastapi-book-db` container status as `Exit 0` (Stopped), identifying the root cause.

## Alert Evidence
The following alert was active and evaluated as firing:
*   **Alert Name**: `APIUnavailable`
*   **State**: `firing`
*   **Severity**: `critical`
*   **Annotations**:
    *   *Summary*: "Book API is not ready"
    *   *Description*: "The Book API has remained unavailable for longer than 15 seconds. Investigate the API and database dependency."

![Alerts in prometheus firing](screenshots/Alerts%20in%20prometheus%20firing.png)

## Grafana Evidence
![Alerts firing](screenshots/Alerts%20firing.png)
![Simulate DB failure](screenshots/Simulate%20DB%20failure.png)

## Assessment Mapping
This evidence demonstrates:
*   **Early Detection**: The SRE availability alert `APIUnavailable` successfully fired within 20.5 seconds, mapping directly to early detection requirements.
*   **Effective Investigation**: The combination of readiness metrics, structured log socket exceptions, and Docker Compose status allowed rapid diagnosis of the stopped PostgreSQL container dependency.
