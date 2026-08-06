# Outage Evidence: Recovery and Validation

This document contains evidence of manual database container recovery and full validation checks.

## 1. Targeted Recovery Command
```bash
docker compose start db
```
Output:
```text
Container fastapi-book-db Starting
Container fastapi-book-db Started
```

## 2. Database Logs
```bash
docker compose logs --tail=2 db
```
Output:
```text
2026-08-06 02:05:06.994 UTC [1] LOG:  database system is ready to accept connections
```

## 3. Liveness Check
```bash
curl -i http://localhost:8000/health
```
Output:
```http
HTTP/1.1 200 OK
content-type: application/json

{"status":"healthy"}
```

## 4. Readiness Check (Restored automatically)
```bash
curl -i http://localhost:8000/ready
```
Output:
```http
HTTP/1.1 200 OK
content-type: application/json

{"status":"ready"}
```

## 5. Write and Read Functional Check
Create book:
```bash
curl -i -X POST -H "Content-Type: application/json" -d '{"id": 4, "title": "The Silmarillion", "author": "J.R.R. Tolkien", "publication_year": 1977, "genre": "Fantasy"}' http://localhost:8000/api/v1/books/
```
Output:
```http
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"The Silmarillion","author":"J.R.R. Tolkien","publication_year":1977,"genre":"Fantasy"}
```

Read book:
```bash
curl -i http://localhost:8000/api/v1/books/4
```
Output:
```http
HTTP/1.1 200 OK
content-type: application/json

{"id":4,"title":"The Silmarillion","author":"J.R.R. Tolkien","publication_year":1977,"genre":"Fantasy"}
```

## 6. Persistent Data Verification (Existing data intact)
```bash
curl -s http://localhost:8000/api/v1/books/
```
Output:
```json
{"1":{"id":1,"title":"The Hobbit","author":"J.R.R. Tolkien","publication_year":1937,"genre":"Science Fiction"},"2":{"id":2,"title":"The Lord of the Rings","author":"J.R.R. Tolkien","publication_year":1954,"genre":"Fantasy"},"3":{"id":3,"title":"The Return of the King","author":"J.R.R. Tolkien","publication_year":1955,"genre":"Fantasy"},"4":{"id":4,"title":"The Silmarillion","author":"J.R.R. Tolkien","publication_year":1977,"genre":"Fantasy"}}
```
*(Pre-existing books 1, 2, and 3 are present alongside newly created book 4).*

## 7. Prometheus Active Alert Status (Alert is inactive)
Query:
```bash
curl -s http://localhost:9090/api/v1/rules
```
Output:
```json
{"status":"success","data":{"groups":[{"name":"availability-alerts","rules":[{"state":"inactive","name":"APIUnavailable"}]}]}}
```
