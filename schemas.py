from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

# ---------- Базовые сущности ----------
class AuthorBase(BaseModel):
    id: int
    name: str
    sort_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class GenreBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class PublisherBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class LocationBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# ---------- Книга (краткий вид для списка) ----------
class BookSummary(BaseModel):
    id: int
    title: str
    isbn: Optional[str] = None
    status: str
    publication_year: Optional[int] = None
    cover_image_path: Optional[str] = None
    authors: List[AuthorBase] = []
    genres: List[GenreBase] = []
    publisher: Optional[PublisherBase] = None
    location: Optional[LocationBase] = None
    modified_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ---------- Книга (полный вид) ----------
class BookDetail(BookSummary):
    udk: Optional[str] = None
    page_count: Optional[int] = None
    description: Optional[str] = None
    borrower_name: Optional[str] = None
    borrower_address: Optional[str] = None
    borrower_phone: Optional[str] = None
    added_date: Optional[datetime] = None
    user_id: int

    model_config = ConfigDict(from_attributes=True)

# ---------- Список книг с пагинацией ----------
class BookList(BaseModel):
    items: List[BookSummary]
    total: int
    page: int
    size: int
    total_pages: int
# ---------- Создание книги (POST) ----------
class BookCreate(BaseModel):
    title: str
    isbn: Optional[str] = None
    udk: Optional[str] = None
    publication_year: Optional[int] = None
    page_count: Optional[int] = None
    description: Optional[str] = None
    cover_image_path: Optional[str] = None
    status: str = "в наличии"
    borrower_name: Optional[str] = None
    borrower_address: Optional[str] = None
    borrower_phone: Optional[str] = None
    location_id: Optional[int] = None
    publisher_id: Optional[int] = None
    author_ids: List[int] = []
    genre_ids: List[int] = []
    user_id: int  # пока обязательно, позже будет из авторизации

# ---------- Обновление книги (PUT) ----------
class BookUpdate(BaseModel):
    title: Optional[str] = None
    isbn: Optional[str] = None
    udk: Optional[str] = None
    publication_year: Optional[int] = None
    page_count: Optional[int] = None
    description: Optional[str] = None
    cover_image_path: Optional[str] = None
    status: Optional[str] = None
    borrower_name: Optional[str] = None
    borrower_address: Optional[str] = None
    borrower_phone: Optional[str] = None
    location_id: Optional[int] = None
    publisher_id: Optional[int] = None
    author_ids: Optional[List[int]] = None
    genre_ids: Optional[List[int]] = None
