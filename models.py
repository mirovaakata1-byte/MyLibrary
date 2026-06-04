from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(30))
    password_hash = Column(String(255), nullable=False)

class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sort_name = Column(String(255))

class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class Publisher(Base):
    __tablename__ = "publishers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    isbn = Column(String(20), unique=True)
    udk = Column(String(20))
    publication_year = Column(Integer)
    page_count = Column(Integer)
    description = Column(Text)
    cover_image_path = Column(Text)
    status = Column(String(20), nullable=False, default="в наличии")
    borrower_name = Column(String(255))
    borrower_address = Column(Text)
    borrower_phone = Column(String(30))
    added_date = Column(DateTime(timezone=False), server_default=func.now())
    modified_date = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())
    location_id = Column(Integer, ForeignKey("locations.id"))
    publisher_id = Column(Integer, ForeignKey("publishers.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    location = relationship("Location")
    publisher = relationship("Publisher")
    owner = relationship("User")
    authors = relationship("Author", secondary="book_authors")
    genres = relationship("Genre", secondary="book_genres")

class BookAuthor(Base):
    __tablename__ = "book_authors"
    book_id = Column(Integer, ForeignKey("books.id"), primary_key=True)
    author_id = Column(Integer, ForeignKey("authors.id"), primary_key=True)

class BookGenre(Base):
    __tablename__ = "book_genres"
    book_id = Column(Integer, ForeignKey("books.id"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genres.id"), primary_key=True)

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    action = Column(String(50), nullable=False)
    action_timestamp = Column(DateTime(timezone=False), server_default=func.now())