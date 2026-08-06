# Operational Readiness Demo

## Assessment Context
This technical assessment builds upon an existing personal FastAPI book management application. The original application code (which predates this assessment) provided standard CRUD operations for book collections. The assessment work focused entirely on adding operational-readiness capabilities, including:
* Structured JSON logging via custom ASGI middleware.
* Bounded HTTP telemetry metrics scraped by a containerized Prometheus instance.
* Custom dynamic `/health` (liveness) and `/ready` (readiness) check endpoints.
* Availability (`APIUnavailable`) and performance (`APILatencyElevated`) alerts.
* Reversible failure simulation script and operator validation checklists.

## What This Demonstrates
This project directly demonstrates the requirements of **Case Study 3 — Operational Readiness and Recovery**:
*   **Outcome 1 (Observe What Matters)**: Exposing clear structured logs, Prometheus-compatible HTTP counts/duration metrics with bounded path labels to control cardinality, and health/readiness endpoints.
*   **Outcome 2 (Alert and Recover)**: Defining actionable availability alerts (for dependency readiness failure) and performance alerts (for sustained p95 latency breaches), with a safe simulation script to demonstrate detection, triage, targeted recovery, and complete validation.
*   **Outcome 3 (Runbook and Improvement)**: Providing a concise operator-facing incident response runbook (`RUNBOOK.md`) with explicit escalation thresholds, recovery validation criteria, and a concrete preventive improvement.

## Architecture
```text
Client / Assessor
   │
   ▼
FastAPI (api:8000) ───► PostgreSQL (db:5432)
   │
   ├───────────────► stdout (Structured JSON logs)
   │
   └───────────────► Prometheus (prometheus:9090)
                         │
                         └──► Availability & Performance alerts
```
*   **FastAPI Service**: Serves CRUD APIs and dynamic endpoints `/health`, `/ready`, and `/metrics`.
*   **PostgreSQL Database**: Persistent relational backend storage.
*   **Structured JSON Logs**: Written to stdout for collection.
*   **Prometheus Service**: Scrapes API `/metrics` every 5 seconds, evaluating alert rules continuously.

## Quick Start

### Prerequisites
This demonstration assumes you have **Docker** and **Docker Compose** installed locally. If not, please install Docker before executing the commands below.

### Setup Instructions
1. Clone the repository and navigate into the folder:
   ```bash
   git clone https://github.com/GideonIsBuilding/operational-readiness-demo.git
   cd operational-readiness-demo
   cp .env.example .env
   ```
2. Build and start services in detached mode:
   ```bash
   docker compose up -d --build
   ```
3. Verify baseline health:
   ```bash
   curl -i http://localhost:8000/health
   curl -i http://localhost:8000/ready
   ```

## Operational Signals

### Health & Readiness
*   **Liveness (`/health`)**: Confirms the FastAPI API process is running. Query: `curl http://localhost:8000/health` (Expected: `200 OK`).
*   **Readiness (`/ready`)**: Performs a connection ping against the PostgreSQL backend database dependency. Query: `curl http://localhost:8000/ready` (Expected: `200 OK`).

### Structured Logs
All requests and system events write structured JSON lines to stdout with the following core fields:
```json
{"timestamp": "2026-08-06T02:05:38.215000+00:00", "message": "Processed POST /api/v1/books/ - 201", "level": "INFO", "name": "fastapi-book-project", "module": "middleware", "function": "dispatch", "line_number": 55, "taskName": "Task-512", "event_name": "http_request", "http_method": "POST", "path": "/api/v1/books/", "event_status": "success", "http_status": 201, "duration_ms": 11.2}
```
*   *Cardinality/Noise Control*: Probes to `/health`, `/ready`, and `/metrics` returning HTTP status < 400 are suppressed from request logging.

### Metrics
Exposed at `http://localhost:8000/metrics`:
*   `http_requests_total`: Total HTTP requests counter (labels: `method`, `path`, `status_code`).
*   `http_request_duration_seconds`: Request processing duration histogram (labels: `method`, `path`, `status_code`).
*   `http_requests_errors_total`: Request error counter tracking handled/unhandled exceptions.
*   `application_ready`: Gauge signaling database connection status (1.0 = connected, 0.0 = disconnected).
*   *Cardinality Control*: The `path` label is strictly normalized using route templates (e.g. `/api/v1/books/{book_id}`) to prevent unbounded collection from variable IDs.

## Alerts

### Availability
*   **Alert Name**: `APIUnavailable`
*   **Expression**: `application_ready == 0`
*   **For duration**: `15s`
*   **Severity**: `critical`
*   **Meaning**: The application is unable to connect to PostgreSQL and is ineligible to receive traffic.
*   **Operator Action**: Check logs for PostgreSQL socket errors, inspect database container state, and run targeted recovery.

### Performance
*   **Alert Name**: `APILatencyElevated`
*   **Expression**: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) > 0.5`
*   **For duration**: `30s`
*   **Severity**: `warning`
*   **Meaning**: The 95th percentile (p95) API request latency exceeds 500ms for longer than 30 seconds.
*   **Operator Action**: Query the dashboard to find slow paths, check DB locking, and optimize transaction connection pools.

## Failure Simulation
To safely reproduce the database outage scenario locally:
```bash
./scripts/simulate-db-failure.sh
```
*   **What it does**: Verifies baseline environment health, stops the database container (`docker compose stop db`), waits for metrics scrape interval propagation, verifies liveness returns `200` while readiness drops to `503`, queries the pending/firing alert state in Prometheus, and prints SRE operator investigation instructions.

## Recovery
1.  **Start Database Container**:
    ```bash
    docker compose start db
    ```
2.  **Verify Database Health**: Inspect status (`docker compose ps`) and verify container logs show `database system is ready to accept connections`.
3.  **Verify Application Readiness**: Confirm `curl -i http://localhost:8000/ready` returns `200 OK`.
4.  **Verify Write/Read Functionality**:
    ```bash
    curl -i -X POST -H "Content-Type: application/json" -d '{"id": 4, "title": "The Silmarillion", "author": "J.R.R. Tolkien", "publication_year": 1977, "genre": "Fantasy"}' http://localhost:8000/api/v1/books/
    ```
5.  **Verify Data Persistence**: Verify pre-existing seed data (Book IDs 1, 2, 3) is still present.
6.  **Verify Alert Cleared**: Confirm the `APIUnavailable` alert transitions back to `INACTIVE` state.

## Evidence
*   [baseline.md](file:///Users/galosikhena/Downloads/fastapi-book-project/evidence/baseline.md) - Healthy baseline verification.
*   [failure.md](file:///Users/galosikhena/Downloads/fastapi-book-project/evidence/failure.md) - Outage indicators and firing alert state.
*   [recovery.md](file:///Users/galosikhena/Downloads/fastapi-book-project/evidence/recovery.md) - Restored readiness and functional verification proof.
*   [timeline.md](file:///Users/galosikhena/Downloads/fastapi-book-project/evidence/timeline.md) - Chronological SRE incident timeline.

## Runbook
See SRE Operator checklists and escalation paths in the [RUNBOOK.md](file:///Users/galosikhena/Downloads/fastapi-book-project/RUNBOOK.md).

## Security
*   **Secrets**: Excluded database password and secret keys from source control. Saved safe example values in `.env.example` and ignored active overrides via `.gitignore`.
*   **Containers**: Configured the Dockerfile to run the application process as a dedicated non-privileged user (`appuser`), avoiding running as root.
*   **Data**: The setup operates strictly with synthetic mock data.
*   **No Sensitive Logs**: Metric labels and logging payloads do not record authorization headers, credentials, or sensitive request payloads.
*   **Intentionally Deferred**: Production secrets managers (e.g. AWS Secrets Manager or HashiCorp Vault) and TLS certificate rotation are outside the scope of this local Compose environment.

## Trade-offs & Limitations
*   **Compose vs Kubernetes**: Selected Docker Compose to minimize infrastructure complexity on development machines and support a single-command setup.
*   **Pure Python Client**: Used `pg8000` instead of a compiled client (`psycopg2`) to keep the API image tiny and speed up build processes without compiling C dependencies on Alpine.
*   **No Alertmanager**: Notifications (e.g., Slack or PagerDuty integrations) are deferred to keep the SRE stack minimal.
*   **No Distributed Tracing**: Distributed tracing (OpenTelemetry span collections) is omitted due to resource consumption constraints.

## Preventive Improvement
*   **Selected Improvement**: Database connection retries with exponential backoff inside `api/db/schemas.py`.
*   **Why**: Transient connection drops during container restarts or network shifts cause immediate failure checks. Having exponential connection backoffs auto-heals transient drops without failing readiness or triggering page alerts unnecessarily.
*   **Trade-off**: Marginally increases response latency for active queries during retries.

## Cleanup
To stop all containers and tear down the network:
```bash
docker compose down
```
To destroy all persistent PostgreSQL storage volumes:
```bash
docker compose down -v
```

## Attribution / Project History
**Clear Disclosure**: The underlying FastAPI book CRUD application code predates this DevOps/SRE assessment. The work done during this assessment is focused strictly on adding SRE operational readiness features, telemetry instrumentation, alerts configuration, and incident recovery testing.
