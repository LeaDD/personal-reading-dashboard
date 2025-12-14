import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.book_model import Book
from backend.app.schemas.books_schema import CSVBook


logger = logging.getLogger(__name__)

def delete_books(books: list[CSVBook], db: Session) -> dict[str, int]:
    """
    Delete books from the database that are no longer in the CSV export.
    
    Compares incoming CSV book list with existing database records and
    deletes any books that are present in the database but not in the
    incoming CSV (indicating they were removed from Goodreads library).
    
    Args:
        books: List of CSVBook objects from the CSV export
        db: Database session
    
    Returns:
        dict with count of books deleted: {"books_deleted": int}
    """
    count = 0
    if books:
        try:
            # Get all existing Goodreads IDs
            incoming_ids = [book_id for book in books if (book_id := book.goodreads_id)]

            books_to_delete = db.query(Book).filter(Book.goodreads_id.not_in(incoming_ids)).all()
            for book in books_to_delete:
                count += 1
                logger.info(f"Deleting entry for {book.title}.")
                db.delete(book)
                
            if count > 0:
                db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error deleting books: {e}")
            raise
    else:
        logger.info("No books passed for update evaluation.")

    return {"books_deleted": count}

if __name__ == "__main__":
    from backend.app.services.csv_parser import parse_goodreads_csv
    from backend.app.config.logging_config import setup_logging
    from backend.app.database import SessionLocal

    # Enable logging
    setup_logging()

    # Bring in the Goodreads records
    csv_books = parse_goodreads_csv("test_data/goodreads_library_export.csv")

    with SessionLocal() as db:
        delete_books(csv_books, db)