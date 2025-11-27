from backend.app.schemas.books_schema import CSVBook, BookCreate
import logging 
from pydantic import ValidationError

logger = logging.getLogger(__name__)

def transform_book(book: CSVBook, google_books_data: dict | None) -> BookCreate:
    """
    Transform a CSVBook object into a BookCreate object.
    """
    logger.info(f"Transforming book {book.title} by {book.author}")
    try:
        if google_books_data:
            # Use CSV page count as primary, fall back to Google Books
            page_count = book.num_pages if book.num_pages else google_books_data.get("page_count")
            
            transformed_book = BookCreate(
                google_books_id=google_books_data.get("google_books_id"),
                google_books_link=google_books_data.get("google_books_link"),
                title=book.title if book.title else google_books_data.get("title"),
                authors=google_books_data.get("authors"),
                published_date=google_books_data.get("published_date"),
                year_published=google_books_data.get("year_published"),
                page_count=page_count,
                categories=google_books_data.get("categories"),
                genre=google_books_data.get("genre"),
                description=google_books_data.get("description"),
                isbn_10=google_books_data.get("isbn_10"),
                isbn_13=google_books_data.get("isbn_13"),
                small_thumbnail=google_books_data.get("small_thumbnail"),
                thumbnail=google_books_data.get("thumbnail"),
                status=book.status,
                goodreads_id=book.goodreads_id,
                finish_date=book.finish_date,
            )            
        else:
            logger.warning(f"No Google Books data found for {book.title} by {book.author}. Creating BookCreate from CSV data only.")
            transformed_book = BookCreate(
                title=book.title,
                authors=[book.author],
                page_count=book.num_pages,
                status=book.status,
                goodreads_id=book.goodreads_id,
                finish_date=book.finish_date,
            )
        return transformed_book
    
    except ValidationError as e:
        logger.error(f"Error transforming book {book.title} by {book.author}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error transforming book {book.title} by {book.author}: {e}")
        raise