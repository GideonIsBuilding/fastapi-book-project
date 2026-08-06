# Recovery and Validation

## Recovery Action
To restore the failed PostgreSQL container dependency, the operator executed the following targeted command:
```bash
docker compose start db
```
*   *Note*: The database volume `db-data` was not deleted or modified, preserving all persistent records.

## Recovery Observation
Following the database restoration, the following signals were observed:
*   **PostgreSQL connectivity restored**: The database engine reported accepting connections within 4 seconds.
*   **Application readiness restored**: The API automatically reconnected. `/ready` returned `HTTP 200 OK` within 12 seconds.
*   **Alert cleared**: The `APIUnavailable` alert cleared back to `inactive` state on the first scrape cycle.
*   **HTTP errors returned toward baseline**: Request connection timeouts ceased, and success counts resumed.
*   **Latency**: Average endpoint latency returned to baseline levels (~16ms).

## Validation
The operator validated the complete recovery of the environment using the following validation checklist:
1.  **Readiness Probe**:
    ```bash
    curl -i http://localhost:8000/ready
    ```
    *   *Observed Output*: `HTTP 1.1 200 OK` with JSON `{"status":"ready"}`.
2.  **API Functional Write/Read**:
    Created a new book record using `POST` and fetched it using `GET`:
    ```bash
    curl -i -X POST -H "Content-Type: application/json" -d '{"id": 4, "title": "The Silmarillion", "author": "J.R.R. Tolkien", "publication_year": 1977, "genre": "Fantasy"}' http://localhost:8000/api/v1/books/
    ```
    *   *Observed Output*: `HTTP 1.1 201 Created` with the JSON record.
3.  **Data Integrity Check**:
    Verified that pre-existing seed data (Book IDs 1, 2, 3) remained available:
    ```bash
    curl -s http://localhost:8000/api/v1/books/
    ```
4.  **Prometheus & Alert State**:
    Confirmed target is `UP` and `APIUnavailable` alert transitioned to `INACTIVE`.

## Evidence
![DB connection restored](screenshots/DB%20connection%20restored.png)
![Alerts cleared](screenshots/Alerts%20cleared.png)

## Recovery Outcome
The recovery was fully successful. The application reconnected to the database automatically without process restarts, persistent volumes preserved all book data, and SRE alerts cleared to an inactive state.

## Assessment Mapping
This evidence demonstrates:
*   **SRE Recovery**: Targeted restart of only the failed dependency container minimizes outage duration and validates pool reconnection.
*   **System Validation**: Performing end-to-end database-backed read/write tests confirms the service is fully functional rather than just process-live.
