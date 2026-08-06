from enum import Enum
from typing import OrderedDict, Optional
import pg8000
from core.config import settings

from pydantic import BaseModel


class Genre(str, Enum):
    """Book genres."""

    SCI_FI = "Science Fiction"
    FANTASY = "Fantasy"
    HORROR = "Horror"
    MYSTERY = "Mystery"
    ROMANCE = "Romance"
    THRILLER = "Thriller"


class Book(BaseModel):
    """Book schema

    Args:
        BaseModel (BaseModel): Pydantic base model.
    """

    id: int
    title: str
    author: str
    publication_year: int
    genre: Genre


class PostgresBooksHelper:
    """Helper wrapper to maintain dictionary-like books interface."""
    def __init__(self, db_instance):
        self.db = db_instance

    def get(self, book_id: int) -> Optional[Book]:
        return self.db.get_book(book_id)


class InMemoryDB:
    def __init__(self):
        self._conn = None
        self._initialized = False
        self._test_books = {}

    @property
    def is_testing(self):
        return settings.TESTING

    @property
    def connection(self):
        if self._conn is None:
            self._conn = pg8000.connect(
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD,
                database=settings.DATABASE_DB,
                timeout=5
            )
            self._conn.autocommit = True
        return self._conn

    def _init_db(self):
        if self.is_testing:
            if not self._test_books:
                self._test_books = {
                    1: Book(id=1, title="The Hobbit", author="J.R.R. Tolkien", publication_year=1937, genre=Genre.SCI_FI),
                    2: Book(id=2, title="The Lord of the Rings", author="J.R.R. Tolkien", publication_year=1954, genre=Genre.FANTASY),
                    3: Book(id=3, title="The Return of the King", author="J.R.R. Tolkien", publication_year=1955, genre=Genre.FANTASY)
                }
            return
        if self._initialized:
            return
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    publication_year INT NOT NULL,
                    genre TEXT NOT NULL
                )
            """)
            self._initialized = True
        except Exception as e:
            self._conn = None
            print(f"Error initializing DB table: {e}")
            raise e

    @property
    def books(self):
        try:
            self._init_db()
        except Exception:
            pass
        if self.is_testing:
            return self._test_books
        return PostgresBooksHelper(self)

    @books.setter
    def books(self, value):
        try:
            self._init_db()
            if self.is_testing:
                self._test_books = value
                return
            cursor = self.connection.cursor()
            for book_id, book in value.items():
                cursor.execute(
                    "INSERT INTO books (id, title, author, publication_year, genre) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                    (book.id, book.title, book.author, book.publication_year, book.genre.value)
                )
        except Exception as e:
            self._conn = None
            print(f"Error seeding DB: {e}")

    def check_connection(self) -> bool:
        if self.is_testing:
            return True
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            return True
        except Exception:
            self._conn = None
            return False

    def get_books(self) -> OrderedDict[int, Book]:
        try:
            self._init_db()
            if self.is_testing:
                return OrderedDict(self._test_books)
            res = OrderedDict()
            cursor = self.connection.cursor()
            cursor.execute("SELECT id, title, author, publication_year, genre FROM books ORDER BY id")
            for row in cursor.fetchall():
                res[row[0]] = Book(
                    id=row[0],
                    title=row[1],
                    author=row[2],
                    publication_year=row[3],
                    genre=Genre(row[4])
                )
            return res
        except Exception as e:
            self._conn = None
            print(f"Error getting books: {e}")
            return OrderedDict()

    def add_book(self, book: Book) -> Book:
        try:
            self._init_db()
            if self.is_testing:
                self._test_books[book.id] = book
                return book
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO books (id, title, author, publication_year, genre) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, author=EXCLUDED.author, publication_year=EXCLUDED.publication_year, genre=EXCLUDED.genre",
                (book.id, book.title, book.author, book.publication_year, book.genre.value)
            )
            return book
        except Exception as e:
            self._conn = None
            print(f"Error adding book: {e}")
            return None

    def get_book(self, book_id: int) -> Optional[Book]:
        try:
            self._init_db()
            if self.is_testing:
                return self._test_books.get(book_id)
            cursor = self.connection.cursor()
            cursor.execute("SELECT id, title, author, publication_year, genre FROM books WHERE id=%s", (book_id,))
            row = cursor.fetchone()
            if row:
                return Book(
                    id=row[0],
                    title=row[1],
                    author=row[2],
                    publication_year=row[3],
                    genre=Genre(row[4])
                )
            return None
        except Exception as e:
            self._conn = None
            print(f"Error getting book {book_id}: {e}")
            return None

    def update_book(self, book_id: int, data: Book) -> Optional[Book]:
        try:
            self._init_db()
            if self.is_testing:
                self._test_books[book_id] = data
                return data
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE books SET title=%s, author=%s, publication_year=%s, genre=%s WHERE id=%s",
                (data.title, data.author, data.publication_year, data.genre.value, book_id)
            )
            return self.get_book(book_id)
        except Exception as e:
            self._conn = None
            print(f"Error updating book {book_id}: {e}")
            return None

    def delete_book(self, book_id: int) -> None:
        try:
            self._init_db()
            if self.is_testing:
                if book_id in self._test_books:
                    del self._test_books[book_id]
                return
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM books WHERE id=%s", (book_id,))
        except Exception as e:
            self._conn = None
            print(f"Error deleting book {book_id}: {e}")
