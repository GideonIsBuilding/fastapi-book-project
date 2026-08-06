from tests import client


def test_get_all_books(caplog):
    with caplog.at_level("INFO"):
        response = client.get("/books/")
        assert response.status_code == 200
        assert len(response.json()) == 3
        
        # Verify middleware HTTP log
        http_logs = [r for r in caplog.records if getattr(r, "event_name", None) == "http_request"]
        assert len(http_logs) == 1
        assert http_logs[0].http_method == "GET"
        assert http_logs[0].http_status == 200


def test_get_single_book(caplog):
    with caplog.at_level("INFO"):
        response = client.get("/books/1")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "The Hobbit"
        assert data["author"] == "J.R.R. Tolkien"
        
        # Verify route log
        route_logs = [r for r in caplog.records if getattr(r, "event_name", None) == "get_book_by_id"]
        assert len(route_logs) == 1
        assert route_logs[0].book_id == 1


def test_create_book(caplog):
    new_book = {
        "id": 4,
        "title": "Harry Potter and the Sorcerer's Stone",
        "author": "J.K. Rowling",
        "publication_year": 1997,
        "genre": "Fantasy",
    }
    with caplog.at_level("INFO"):
        response = client.post("/books/", json=new_book)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 4
        assert data["title"] == "Harry Potter and the Sorcerer's Stone"
        
        # Verify custom endpoint event log
        create_logs = [r for r in caplog.records if getattr(r, "event_name", None) == "create_book"]
        assert len(create_logs) == 1
        assert create_logs[0].book_id == 4
        assert create_logs[0].genre == "Fantasy"


def test_update_book(caplog):
    updated_book = {
        "id": 1,
        "title": "The Hobbit: An Unexpected Journey",
        "author": "J.R.R. Tolkien",
        "publication_year": 1937,
        "genre": "Fantasy",
    }
    with caplog.at_level("INFO"):
        response = client.put("/books/1", json=updated_book)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "The Hobbit: An Unexpected Journey"
        
        # Verify update event log
        update_logs = [r for r in caplog.records if getattr(r, "event_name", None) == "update_book"]
        assert len(update_logs) == 1
        assert update_logs[0].book_id == 1
        assert update_logs[0].genre == "Fantasy"


def test_delete_book(caplog):
    with caplog.at_level("INFO"):
        response = client.delete("/books/3")
        assert response.status_code == 204

        # Verify delete log
        delete_logs = [r for r in caplog.records if getattr(r, "event_name", None) == "delete_book"]
        assert len(delete_logs) == 1
        assert delete_logs[0].book_id == 3

        response = client.get("/books/3")
        assert response.status_code == 404


def test_get_nonexistent_book_warning(caplog):
    with caplog.at_level("WARNING"):
        response = client.get("/books/999")
        assert response.status_code == 404
        
        # Verify warning log for non-existent book
        warning_logs = [r for r in caplog.records if getattr(r, "event_name", None) == "book_not_found"]
        assert len(warning_logs) == 1
        assert warning_logs[0].book_id == 999
        assert warning_logs[0].levelname == "WARNING"


def get_metric_value(metric_name, label_filters=None):
    from prometheus_client import REGISTRY
    for metric in REGISTRY.collect():
        for sample in metric.samples:
            if sample.name == metric_name:
                if label_filters:
                    match = all(sample.labels.get(k) == v for k, v in label_filters.items())
                    if match:
                        return sample.value
                else:
                    return sample.value
    return 0.0


def test_metrics_endpoint_exposes_prometheus_format():
    response = client.get("http://test/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
    assert "http_requests_errors_total" in response.text
    assert response.headers["content-type"].startswith("text/plain")


def test_successful_request_increments_request_counter():
    labels = {"method": "GET", "path": "/api/v1/books/", "status_code": "200"}
    before = get_metric_value("http_requests_total", labels)
    
    response = client.get("/books/")
    assert response.status_code == 200
    
    after = get_metric_value("http_requests_total", labels)
    assert after == before + 1


def test_failed_request_increments_error_counter():
    labels = {"method": "GET", "path": "/error", "status_code": "500"}
    before_total = get_metric_value("http_requests_total", labels)
    before_errors = get_metric_value("http_requests_errors_total", labels)
    
    from fastapi.testclient import TestClient
    from main import app
    err_client = TestClient(app, raise_server_exceptions=False)
    response = err_client.get("/error")
    assert response.status_code == 500
    
    after_total = get_metric_value("http_requests_total", labels)
    after_errors = get_metric_value("http_requests_errors_total", labels)
    
    assert after_total == before_total + 1
    assert after_errors == before_errors + 1


def test_request_duration_seconds_is_recorded():
    labels = {"method": "GET", "path": "/api/v1/books/", "status_code": "200"}
    before_count = get_metric_value("http_request_duration_seconds_count", labels)
    
    response = client.get("/books/")
    assert response.status_code == 200
    
    after_count = get_metric_value("http_request_duration_seconds_count", labels)
    assert after_count == before_count + 1


def test_health_endpoint_returns_healthy_200():
    response = client.get("http://test/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready_endpoint_returns_ready_200_when_db_up():
    response = client.get("http://test/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_endpoint_returns_503_on_db_down():
    from unittest.mock import patch
    from api.routes.books import db
    with patch.object(db, "check_connection", return_value=False):
        response = client.get("http://test/ready")
        assert response.status_code == 503
        data = response.json()
        assert data == {"status": "not_ready", "reason": "database_unavailable"}


def test_readiness_metric_reports_ready_and_not_ready():
    # Call metrics endpoint to update the registry state
    client.get("http://test/metrics")
    assert get_metric_value("application_ready") == 1.0

    # Verify application_ready reports 0.0 when database is mocked as down
    from unittest.mock import patch
    from api.routes.books import db
    with patch.object(db, "check_connection", return_value=False):
        client.get("http://test/metrics")
        assert get_metric_value("application_ready") == 0.0




