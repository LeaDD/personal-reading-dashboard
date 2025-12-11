import logging
from sqlalchemy.orm import Session

from backend.app.services.csv_parser import parse_goodreads_csv
from backend.app.models.book_model import Book
from backend.app.schemas.books_schema import CSVBook
from backend.app.database import SessionLocal


logger = logging.getLogger(__name__)

def deduplicate_books(books: list[CSVBook], db: Session) -> list[CSVBook]:
    """
    Deduplicate books based on Goodreads ID.

    Args:
        books: List of CSVBook objects, each representing a book.
        db: Database session

    Returns:
        List of CSVBook objects, each representing a book that is not already in the database.
    """
    logger.info(f"Deduplicating {len(books)} books")

    try:
        # Check if books are already in the database
        # Get all existing Goodreads IDs
        incoming_goodreads_ids = [book_id for book in books if (book_id := book.goodreads_id)]
        # Get all existing books with the same Goodreads IDs
        existing_books = db.query(Book.goodreads_id).filter(Book.goodreads_id.in_(incoming_goodreads_ids)).all()
        # Get all existing Goodreads IDs into a set for O(1) lookup (more efficient than a list)
        existing_goodreads_ids = {book.goodreads_id for book in existing_books}
        # Get all new books that are not already in the database
        new_books = [book for book in books if book.goodreads_id not in existing_goodreads_ids]
            
    except Exception as e:
        logger.error(f"Unexpected error while deduplicating books: {e}")

    return new_books


if __name__ == "__main__":
    from backend.app.config.logging_config import setup_logging
    setup_logging()

    with SessionLocal() as db:        
        books = parse_goodreads_csv("test_data/goodreads_library_export.csv")
        deduplicated_books = deduplicate_books(books, db)
        logger.info(f"Deduplicated {len(deduplicated_books)} books")
        logger.info(deduplicated_books)

    


