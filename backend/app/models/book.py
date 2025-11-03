from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Date, JSON, Text, DateTime
from backend.app.database import Base
from datetime import date, datetime

class Book(Base):
    __tablename__ = "books"
    
    # Google Books API data
    id: Mapped[int] = mapped_column(primary_key=True, index=True) 
    google_books_id: Mapped[str] = mapped_column(unique=True, nullable=True)
    google_books_link: Mapped[str] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    authors: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    published_date: Mapped[date] = mapped_column(Date, nullable=True)
    year_published: Mapped[int] = mapped_column(Integer, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=True)
    categories: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    genre: Mapped[str] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    isbn_10: Mapped[str] = mapped_column(String(10), nullable=True)
    isbn_13: Mapped[str] = mapped_column(String(13), nullable=True)   
    small_thumbnail: Mapped[str] = mapped_column(String(500), nullable=True)
    thumbnail: Mapped[str] = mapped_column(String(500), nullable=True)

    # Goodreads CSV data
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    goodreads_id: Mapped[str] = mapped_column(String(50), unique=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    finish_date: Mapped[date] = mapped_column(Date, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    