from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from external_api import search_by_isbn
from typing import Optional
import math

from database import get_db
from models import Book, Author, Genre, Publisher, Location, BookAuthor, BookGenre
from schemas import BookSummary, BookDetail, BookList, BookCreate, BookUpdate

app = FastAPI(title="Моя библиотека API")

@app.get("/api/books", response_model=BookList)
async def get_books(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    genre_id: Optional[int] = Query(None),
    author_id: Optional[int] = Query(None),
    location_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Book).options(
        selectinload(Book.authors),
        selectinload(Book.genres),
        selectinload(Book.publisher),
        selectinload(Book.location)
    )

    filters = []
    if status:
        filters.append(Book.status == status)
    if location_id:
        filters.append(Book.location_id == location_id)
    if genre_id:
        query = query.join(BookGenre, Book.id == BookGenre.book_id)
        filters.append(BookGenre.genre_id == genre_id)
    if author_id:
        query = query.join(BookAuthor, Book.id == BookAuthor.book_id)
        filters.append(BookAuthor.author_id == author_id)
    if search:
        search_term = f"%{search}%"
        filters.append(or_(
            Book.title.ilike(search_term),
            Book.isbn.ilike(search_term),
            Book.description.ilike(search_term)
        ))

    if filters:
        query = query.filter(*filters)

    sort_mapping = {
        "title": Book.title,
        "year": Book.publication_year,
        "added": Book.added_date,
    }
    if sort and sort.lstrip("-") in sort_mapping:
        field = sort_mapping[sort.lstrip("-")]
        if sort.startswith("-"):
            query = query.order_by(field.desc())
        else:
            query = query.order_by(field)
    else:
        query = query.order_by(Book.added_date.desc())

    count_query = select(func.count()).select_from(Book)
    if filters:
        count_query = count_query.filter(*filters)
    total = (await db.execute(count_query)).scalar()

    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    books = result.scalars().all()

    total_pages = math.ceil(total / size) if total else 0

    return BookList(
        items=[BookSummary.model_validate(book) for book in books],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@app.get("/api/books/search-external")
async def search_external(isbn: str):
    """Поиск книги по ISBN во внешнем API (Open Library)."""
    if not isbn:
        raise HTTPException(status_code=400, detail="Параметр isbn обязателен")
    result = search_by_isbn(isbn.strip())
    if not result:
        raise HTTPException(status_code=404, detail="Книга с таким ISBN не найдена")
    return result

@app.get("/api/books/{book_id}", response_model=BookDetail)
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Book).options(
        selectinload(Book.authors),
        selectinload(Book.genres),
        selectinload(Book.publisher),
        selectinload(Book.location)
    ).where(Book.id == book_id)
    result = await db.execute(query)
    book = result.scalar()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book

@app.post("/api/books", response_model=BookDetail, status_code=201)
async def create_book(book_data: BookCreate, db: AsyncSession = Depends(get_db)):
    if book_data.isbn:
        existing = await db.execute(select(Book).where(Book.isbn == book_data.isbn))
        if existing.scalar():
            raise HTTPException(status_code=400, detail="Книга с таким ISBN уже существует")

    if book_data.location_id:
        loc = await db.get(Location, book_data.location_id)
        if not loc:
            raise HTTPException(status_code=400, detail=f"Локация с id={book_data.location_id} не найдена")
    if book_data.publisher_id:
        pub = await db.get(Publisher, book_data.publisher_id)
        if not pub:
            raise HTTPException(status_code=400, detail=f"Издатель с id={book_data.publisher_id} не найден")

    book = Book(
        title=book_data.title,
        isbn=book_data.isbn,
        udk=book_data.udk,
        publication_year=book_data.publication_year,
        page_count=book_data.page_count,
        description=book_data.description,
        cover_image_path=book_data.cover_image_path,
        status=book_data.status,
        borrower_name=book_data.borrower_name,
        borrower_address=book_data.borrower_address,
        borrower_phone=book_data.borrower_phone,
        location_id=book_data.location_id,
        publisher_id=book_data.publisher_id,
        user_id=book_data.user_id
    )
    db.add(book)
    await db.flush()

    for author_id in book_data.author_ids:
        author = await db.get(Author, author_id)
        if not author:
            raise HTTPException(status_code=400, detail=f"Автор с id={author_id} не найден")
        db.add(BookAuthor(book_id=book.id, author_id=author_id))

    for genre_id in book_data.genre_ids:
        genre = await db.get(Genre, genre_id)
        if not genre:
            raise HTTPException(status_code=400, detail=f"Жанр с id={genre_id} не найден")
        db.add(BookGenre(book_id=book.id, genre_id=genre_id))

    await db.commit()
    await db.refresh(book)

    query = select(Book).options(
        selectinload(Book.authors),
        selectinload(Book.genres),
        selectinload(Book.publisher),
        selectinload(Book.location)
    ).where(Book.id == book.id)
    result = await db.execute(query)
    created_book = result.scalar()
    return created_book


@app.put("/api/books/{book_id}", response_model=BookDetail)
async def update_book(book_id: int, book_data: BookUpdate, db: AsyncSession = Depends(get_db)):
    query = select(Book).options(
        selectinload(Book.authors),
        selectinload(Book.genres),
        selectinload(Book.publisher),
        selectinload(Book.location)
    ).where(Book.id == book_id)
    result = await db.execute(query)
    book = result.scalar()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    update_data = book_data.model_dump(exclude_unset=True)
    author_ids = update_data.pop("author_ids", None)
    genre_ids = update_data.pop("genre_ids", None)

    for field, value in update_data.items():
        setattr(book, field, value)

    if author_ids is not None:
        await db.execute(BookAuthor.__table__.delete().where(BookAuthor.book_id == book_id))
        for author_id in author_ids:
            author = await db.get(Author, author_id)
            if not author:
                raise HTTPException(status_code=400, detail=f"Автор с id={author_id} не найден")
            db.add(BookAuthor(book_id=book_id, author_id=author_id))

    if genre_ids is not None:
        await db.execute(BookGenre.__table__.delete().where(BookGenre.book_id == book_id))
        for genre_id in genre_ids:
            genre = await db.get(Genre, genre_id)
            if not genre:
                raise HTTPException(status_code=400, detail=f"Жанр с id={genre_id} не найден")
            db.add(BookGenre(book_id=book_id, genre_id=genre_id))

    await db.commit()
    await db.refresh(book)
    return book

@app.delete("/api/books/{book_id}", status_code=204)
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    await db.delete(book)
    await db.commit()
    return None

@app.get("/api/authors")
async def get_authors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Author).order_by(Author.name))
    return result.scalars().all()

@app.get("/api/genres")
async def get_genres(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Genre).order_by(Genre.name))
    return result.scalars().all()

@app.get("/api/publishers")
async def get_publishers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Publisher).order_by(Publisher.name))
    return result.scalars().all()

@app.get("/api/locations")
async def get_locations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Location).order_by(Location.name))
    return result.scalars().all()
# ========== АВТОРЫ ==========
@app.post("/api/authors", status_code=201)
async def create_author(name: str = Query(...), sort_name: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    author = Author(name=name, sort_name=sort_name)
    db.add(author)
    await db.commit()
    await db.refresh(author)
    return author

@app.put("/api/authors/{author_id}")
async def update_author(author_id: int, name: Optional[str] = Query(None), sort_name: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    author = await db.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Автор не найден")
    if name is not None:
        author.name = name
    if sort_name is not None:
        author.sort_name = sort_name
    await db.commit()
    await db.refresh(author)
    return author

@app.delete("/api/authors/{author_id}", status_code=204)
async def delete_author(author_id: int, db: AsyncSession = Depends(get_db)):
    author = await db.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Автор не найден")
    # Проверка, используется ли автор в книгах
    count = (await db.execute(select(func.count()).select_from(BookAuthor).where(BookAuthor.author_id == author_id))).scalar()
    if count:
        raise HTTPException(status_code=409, detail="Нельзя удалить автора, он используется в книгах")
    await db.delete(author)
    await db.commit()
    return None

# ========== ЖАНРЫ ==========
@app.post("/api/genres", status_code=201)
async def create_genre(name: str = Query(...), db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(Genre).where(Genre.name == name))).scalar()
    if existing:
        raise HTTPException(status_code=400, detail="Такой жанр уже существует")
    genre = Genre(name=name)
    db.add(genre)
    await db.commit()
    await db.refresh(genre)
    return genre

@app.put("/api/genres/{genre_id}")
async def update_genre(genre_id: int, name: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    genre = await db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Жанр не найден")
    if name is not None:
        genre.name = name
    await db.commit()
    await db.refresh(genre)
    return genre

@app.delete("/api/genres/{genre_id}", status_code=204)
async def delete_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    genre = await db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Жанр не найден")
    count = (await db.execute(select(func.count()).select_from(BookGenre).where(BookGenre.genre_id == genre_id))).scalar()
    if count:
        raise HTTPException(status_code=409, detail="Нельзя удалить жанр, он используется в книгах")
    await db.delete(genre)
    await db.commit()
    return None

# ========== ИЗДАТЕЛИ ==========
@app.post("/api/publishers", status_code=201)
async def create_publisher(name: str = Query(...), db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(Publisher).where(Publisher.name == name))).scalar()
    if existing:
        raise HTTPException(status_code=400, detail="Такой издатель уже существует")
    publisher = Publisher(name=name)
    db.add(publisher)
    await db.commit()
    await db.refresh(publisher)
    return publisher

@app.put("/api/publishers/{publisher_id}")
async def update_publisher(publisher_id: int, name: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    publisher = await db.get(Publisher, publisher_id)
    if not publisher:
        raise HTTPException(status_code=404, detail="Издатель не найден")
    if name is not None:
        publisher.name = name
    await db.commit()
    await db.refresh(publisher)
    return publisher

@app.delete("/api/publishers/{publisher_id}", status_code=204)
async def delete_publisher(publisher_id: int, db: AsyncSession = Depends(get_db)):
    publisher = await db.get(Publisher, publisher_id)
    if not publisher:
        raise HTTPException(status_code=404, detail="Издатель не найден")
    count = (await db.execute(select(func.count()).select_from(Book).where(Book.publisher_id == publisher_id))).scalar()
    if count:
        raise HTTPException(status_code=409, detail="Нельзя удалить издателя, он используется в книгах")
    await db.delete(publisher)
    await db.commit()
    return None

# ========== ЛОКАЦИИ ==========
@app.post("/api/locations", status_code=201)
async def create_location(name: str = Query(...), description: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    location = Location(name=name, description=description)
    db.add(location)
    await db.commit()
    await db.refresh(location)
    return location

@app.put("/api/locations/{location_id}")
async def update_location(location_id: int, name: Optional[str] = Query(None), description: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    location = await db.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    if name is not None:
        location.name = name
    if description is not None:
        location.description = description
    await db.commit()
    await db.refresh(location)
    return location

@app.delete("/api/locations/{location_id}", status_code=204)
async def delete_location(location_id: int, db: AsyncSession = Depends(get_db)):
    location = await db.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    count = (await db.execute(select(func.count()).select_from(Book).where(Book.location_id == location_id))).scalar()
    if count:
        raise HTTPException(status_code=409, detail="Нельзя удалить локацию, она используется в книгах")
    await db.delete(location)
    await db.commit()
    return None
