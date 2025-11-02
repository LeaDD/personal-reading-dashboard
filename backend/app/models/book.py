from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Date, DateTime
from sqlalchemy.sql import func
from backend.app.database import Base
from datetime import date, datetime

class Book(Base):
    __tablename__ = "books"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    goodreads_id: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    genre: Mapped[str] = mapped_column(String(100), nullable=True)
    pages: Mapped[int] = mapped_column(Integer, nullable=True)
    year_published: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    finish_date: Mapped[date] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(Date, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(Date, default=datetime.now, onupdate=datetime.now)

    