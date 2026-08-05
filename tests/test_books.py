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

