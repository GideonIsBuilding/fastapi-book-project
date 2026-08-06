# Baseline

## Purpose
Establish the known-good state before failure injection.

## Environment
The testing is conducted entirely locally using Docker Compose. The environment consists of the following components:
*   `fastapi-book-api`: The FastAPI application container exposing APIs on port `8000`.
*   `fastapi-book-db`: The PostgreSQL backend database container exposing standard socket port `5432` internally.
*   `fastapi-book-prometheus`: The monitoring agent scraping `/metrics` on port `9090`.
*   `fastapi-book-grafana`: The visualization dashboard console on port `3000`.

## Expected Healthy State
When the environment is fully operational:
*   **Application readiness**: `/ready` endpoint returns HTTP status `200 OK`.
*   **PostgreSQL connectivity**: Database connection successfully established by the API.
*   **Active alerts**: Both SRE alert rules (`APIUnavailable`, `APILatencyElevated`) reside in an `inactive` evaluation state.
*   **HTTP request behaviour**: Requests return successful standard responses (e.g. `200` or `201`).
*   **Latency**: The 95th percentile request latency stays well below the 500ms warning threshold.

## Observed Baseline
The following logs and query outputs demonstrate the healthy baseline state:

1.  **Liveness and Readiness Check**:
    *   `GET /health` → `200 OK` (`{"status":"healthy"}`)
    *   `GET /ready` → `200 OK` (`{"status":"ready"}`)
2.  **API Data Retrieval Check**:
    *   `GET /api/v1/books/` returned the complete list of seed books (IDs 1, 2, and 3) successfully.
3.  **Prometheus Target Health**:
    *   Prometheus targets query `/api/v1/targets` verified active targets:
        ```json
        {"status":"success","data":{"activeTargets":[{"labels":{"instance":"api:8000","job":"fastapi-app"},"health":"up"}]}}
        ```
4.  **Alert Rules Status**:
    *   Prometheus query `/api/v1/rules` returned alert states:
        *   `APIUnavailable`: `inactive`
        *   `APILatencyElevated`: `inactive`

## Evidence
![Service is healthy](screenshots/Service%20is%20healthy.png)
