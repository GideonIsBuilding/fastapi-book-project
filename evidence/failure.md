# Outage Evidence: Database Outage State

This document contains evidence of the system behavior after the PostgreSQL database dependency was stopped.

## 1. Container Status
```text
NAME                      IMAGE                      STATUS
fastapi-book-api          fastapi-book-project-api   Up
fastapi-book-prometheus   prom/prometheus:v2.52.0    Up
# fastapi-book-db container is Stopped/Absent from active processes list
```

## 2. Liveness Check (FastAPI remains alive)
```bash
curl -i http://localhost:8000/health
```
Output:
```http
HTTP/1.1 200 OK
content-type: application/json

{"status":"healthy"}
```

## 3. Readiness Check (Correctly registers dependency loss)
```bash
curl -i http://localhost:8000/ready
```
Output:
```http
HTTP/1.1 503 Service Unavailable
content-type: application/json

{"status":"not_ready","reason":"database_unavailable"}
```

## 4. API Error Logs
```bash
docker compose logs --tail=10 api
```
Output:
```text
Error getting books: Can't create a connection to host db and port 5432 (timeout is 5 and source_address is None).
{"timestamp": "2026-08-06T01:29:26.345193+00:00", "message": "Processed GET /ready - 503", "level": "INFO", "name": "fastapi-book-project", "module": "middleware", "function": "dispatch", "line_number": 55, "taskName": "Task-434", "event_name": "http_request", "http_method": "GET", "path": "/ready", "event_status": "success", "http_status": 503, "duration_ms": 17.15}
```

## 5. Prometheus Active Alert Status (Alert is firing)
Query:
```bash
curl -s http://localhost:9090/api/v1/rules
```
Output:
```json
{"status":"success","data":{"groups":[{"name":"availability-alerts","rules":[{"state":"firing","name":"APIUnavailable","alerts":[{"state":"firing","activeAt":"2026-08-06T01:56:27.534998931Z"}]}]}]}}
```
