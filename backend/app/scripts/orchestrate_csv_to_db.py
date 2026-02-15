from backend.app.services.csv_parser import parse_goodreads_csv
from backend.app.services.deduplication import deduplicate_books
from backend.app.services.google_books import get_google_books_data
from backend.app.services.book_transformer import transform_book
from backend.app.services.ingest_books_to_db import ingest_books_to_db
from backend.app.services.update_books import update_books
from backend.app.services.delete_books import delete_books
from backend.app.database import SessionLocal
import logging
import re
import time

logger = logging.getLogger(__name__)

def orchestrate_csv_to_db(csv_file_path: str) -> None:
    """
    Orchestrate the full pipeline from Goodreads CSV to database.
    
    Processes a Goodreads CSV export file through the following steps:
    1. Parse CSV file into CSVBook objects
    2. Deduplicate books (filter out books already in database)
    3. For each new book:
       - Enrich with Google Books metadata
       - Transform CSVBook + Google Books data into BookCreate objects
    4. Ingest all BookCreate objects to database in batches
    
    Books are ingested in batches of 100 to optimize database performance and
    provide better error recovery (if one batch fails, previous batches are saved).
    
    Args:
        csv_file_path: Path to the Goodreads CSV export file (relative to project root)
        
    Returns:
        None
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        Exception: If database operation fails (errors are logged)
        
    Note:
        Individual book processing errors (Google Books API failures, transformation errors)
        are logged but don't stop the pipeline. Only critical errors (CSV parsing, DB connection)
        will raise exceptions.
    """
    logger.info(f"Orchestrating CSV to DB for {csv_file_path}")

    books = parse_goodreads_csv(csv_file_path)
    logger.info(f"Parsed {len(books)} books from CSV")

    with SessionLocal() as db:

        # Update any books which have had a status change
        update_books(books, db)
        # Delete any books which no longer appear in the inbound Goodreads list
        delete_books(books, db)

        # For enrichment and insert get only incoming books which do not already exist in the db.\
        new_books = deduplicate_books(books, db)
        logger.info(f"Deduplicated {len(new_books)} books (removed {len(books) - len(new_books)} duplicates)")
        
        transformed_books = []
        failed_books = []
        
        for i, book in enumerate(new_books, 1):
            try:
                clean_title = re.sub(r'\s*\([^)]*\)', '', book.title).strip()        
                # Get data to enrich book entry from Google books
                enriched_book = get_google_books_data(clean_title, book.author, book.isbn_10, book.isbn_13)
                # Take elements from Goodreads and Google books to create a complete entry and transform into BookCreate Pydantic schema
                transformed_book = transform_book(book, enriched_book)
                transformed_books.append(transformed_book)
                
                # Add delay to avoid rate limiting (0.5 seconds between calls)
                if i < len(new_books):  # Don't delay after the last book
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to process book '{book.title}' by {book.author} (Goodreads ID: {book.goodreads_id}): {e}")
                failed_books.append(book)
                continue
        
        logger.info(f"Successfully transformed {len(transformed_books)} books, {len(failed_books)} failed")
        if failed_books:
            logger.warning(f"Failed books: {[f'{b.title} by {b.author}' for b in failed_books]}")

        
        batch_size = 100
        for i in range(0, len(transformed_books), batch_size):
            batch = transformed_books[i:i+batch_size]
            ingest_books_to_db(batch, db)
        
        logger.info(f"Orchestration complete. Total parsed: {len(books)}, New books: {len(new_books)}, Successfully ingested: {len(transformed_books)}, Failed: {len(failed_books)}")


if __name__ == "__main__":
    import sys
    from backend.app.config.logging_config import setup_logging

    setup_logging()
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "test_data/goodreads_library_export.csv"
    orchestrate_csv_to_db(csv_path)
