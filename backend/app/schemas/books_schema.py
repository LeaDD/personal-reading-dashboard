from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class BookCreate(BaseModel):
    google_books_id: str | None = Field(None, description="The ID of the book in the Google Books API")
    google_books_link: str | None = Field(None, description="The link to the book in the Google Books API")
    title: str = Field(..., description="The title of the book")
    authors: list[str] = Field(..., description="The authors of the book")
    # These date field values will come in from request body as a string and will be parsed to a date object   
    published_date: date | None = Field(None, description="The published date of the book")
    year_published: int | None= Field(None, description="The year the book was published")
    page_count: int | None = Field(None, description="The number of pages in the book")
    categories: list[str] | None = Field(None, description="The categories of the book")
    genre: str | None = Field(None, description="The genre of the book")
    description: str | None = Field(None, description="The description of the book")
    isbn_10: str | None = Field(None, description="The ISBN-10 of the book")
    isbn_13: str | None = Field(None, description="The ISBN-13 of the book")
    small_thumbnail: str | None = Field(None, description="The small thumbnail of the book")
    thumbnail: str | None = Field(None, description="The thumbnail of the book")
    status: str = Field(..., description="The read status of the book e.g. read, reading, want-to-read")
    goodreads_id: str = Field(..., description="The ID of the book in the Goodreads API")
    finish_date: date | None = Field(None, description="The date the book was finished")

class CSVBook(BaseModel):
    title: str = Field(..., description="The title of the book")
    author: str = Field(..., description="The author of the book")
    isbn_10: str | None = Field(None, description="The ISBN-10 of the book")
    isbn_13: str | None = Field(None, description="The ISBN-13 of the book")
    additional_authors: str | None = Field(None, description="Additional authors of the book")
    num_pages: int | None = Field(None, description="The number of pages in the book")
    goodreads_id: str = Field(..., description="The ID of the book in the Goodreads API")
    status: Literal["read", "currently-reading", "to-read"] = Field("to-read", description="The read status of the book e.g. read, currently-reading, want-to-read")
    finish_date: date | None = Field(None, description="The date the book was finished")

class BookResponse(BookCreate):
    # ConfigDict needed to convert SQLAlchemy instances with attributes to Pydantic schema
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique book ID in DB.")
    created_at: datetime = Field(..., description="DB record creation timestamp.")
    updated_at: datetime = Field(..., description="DB record updated timestamp.")
    
class GenreCount(BaseModel):
    """Nested schema for genre breakdown items - more type-safe than list[dict]"""
    genre: str = Field(..., description="Genre name")
    books_count: int = Field(..., description="Number of books in this genre")
    pages_count: int = Field(..., description="Total pages read in this genre")

class StatsResponse(BaseModel):
    total_pages_read: int = Field(..., description="Sum of page count in all read books.")
    total_books_read: int = Field(..., description="Count of all read books.")
    avg_pages_per_book: float = Field(..., description="Average page count of all read books.")
    genre_breakdown: list[GenreCount] = Field(..., description="Count of pages and books by genre.")

class TrendsResponse(BaseModel):
    year_read: str = Field(..., description="Year in which reading was completed.")
    month_read: str = Field(..., description="Month in which reading was completed.")
    pages_read: int = Field(..., description="Count of pages read for corresponding period.")
    books_read: int = Field(..., description="Count of books read for corresponding period.")
    genre: str = Field(..., description="Genre of books read.")