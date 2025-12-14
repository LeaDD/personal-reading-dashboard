import logging 
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.book_model import Book
from backend.app.schemas.books_schema import CSVBook

logger = logging.getLogger(__name__)

def update_books(books: list[CSVBook], db: Session) -> dict[str, int]:
    """
    Update book statuses in the database for books that have changed.
    
    Compares incoming CSV book statuses with existing database records and
    updates any books where the status has changed.
    
    Args:
        books: List of CSVBook objects from the CSV export
        db: Database session
    
    Returns:
        dict with count of books updated: {"books_updated": int}
    """
    try:
        # Get all existing Goodreads IDs
        incoming_books = [(book_id, book.status) for book in books if (book_id := book.goodreads_id)]
        incoming_ids = [book_id for book_id, _ in incoming_books]

        # Initialize count of books updated
        count = 0
        if books:
            try:
                # Get all existing books that having a matching goodreads_id in the incoming list.
                existing_books = db.query(Book).filter(Book.goodreads_id.in_(incoming_ids)).all()
                existing_books_dict = {book.goodreads_id: book for book in existing_books}
                # Iterate through the incoming books and check for any status mismatch against the existing book.
                # If status is changed save and log.
                for goodreads_id, new_status in incoming_books:       
                    existing_book = existing_books_dict.get(goodreads_id)
                    if existing_book and existing_book.status != new_status:  
                        count += 1
                        logger.info(f"Status for goodreads_id {goodreads_id} changed from {existing_book.status} to {new_status}.")
                        existing_book.status = new_status
                if count > 0:
                    db.commit()
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Database error updating books: {e}")
                raise
        else:
            logger.info("No books passed for update evaluation.")

        return {"books_updated": count}
        
    except SQLAlchemyError:
        # Re-raise SQLAlchemy errors (already logged above)
        raise
    except Exception as e:
        logger.error(f"Error updating books: {e}")
        raise

if __name__ == "__main__":    
    from backend.app.services.csv_parser import parse_goodreads_csv
    from backend.app.config.logging_config import setup_logging
    from backend.app.database import SessionLocal

    # Enable logging
    setup_logging()

    # Bring in the Goodreads records
    csv_books = parse_goodreads_csv("test_data/goodreads_library_export.csv")

    # Initialize Session factory
    with SessionLocal() as db:       
        # Perform the updates
        updated_books = update_books(csv_books, db)
        logger.info(updated_books)