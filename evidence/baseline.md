# Outage Evidence: Healthy Baseline

This document contains evidence of the healthy system state prior to simulating the database outage.

## 1. Container Status
```text
NAME                      IMAGE                      STATUS
fastapi-book-api          fastapi-book-project-api   Up
fastapi-book-db           postgres:16-alpine         Up (healthy)
fastapi-book-prometheus   prom/prometheus:v2.52.0    Up
```

## 2. Liveness Check
```bash
curl -i http://localhost:8000/health
```
Output:
```http
HTTP/1.1 200 OK
content-type: application/json

{"status":"healthy"}
```

## 3. Readiness Check
```bash
curl -i http://localhost:8000/ready
```
Output:
```http
HTTP/1.1 200 OK
content-type: application/json

{"status":"ready"}
```

## 4. API Data Retrieval Check
```bash
curl -s http://localhost:8000/api/v1/books/
```
Output:
```json
{"1":{"id":1,"title":"The Hobbit","author":"J.R.R. Tolkien","publication_year":1937,"genre":"Science Fiction"},"2":{"id":2,"title":"The Lord of the Rings","author":"J.R.R. Tolkien","publication_year":1954,"genre":"Fantasy"},"3":{"id":3,"title":"The Return of the King","author":"J.R.R. Tolkien","publication_year":1955,"genre":"Fantasy"}}
```

## 5. Prometheus Target Health
Query:
```bash
curl -s http://localhost:9090/api/v1/targets
```
Output:
```json
{"status":"success","data":{"activeTargets":[{"labels":{"instance":"api:8000","job":"fastapi-app"},"health":"up"}]}}
```

## 6. Prometheus Active Alert Status
Query:
```bash
curl -s http://localhost:9090/api/v1/rules
```
Output:
```json
{"status":"success","data":{"groups":[{"name":"availability-alerts","rules":[{"state":"inactive","name":"APIUnavailable"}]},{"name":"performance-alerts","rules":[{"state":"inactive","name":"APILatencyElevated"}]}]}}
```
