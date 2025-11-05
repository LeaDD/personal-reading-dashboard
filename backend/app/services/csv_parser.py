import csv
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_goodreads_csv(file_path: str) -> list[dict]:
    """
    Parses a Goodreads CSV file and returns a list of books.

    Args:
        file_path (str): Path to the Goodreads CSV file.

    Returns:
        list[dict]: List of dictionaries, each representing a book.
    """
    logger.info(f"Parsing Goodreads CSV file from {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"File {file_path} does not exist")
        raise FileNotFoundError(f"File {file_path} does not exist")

    books = []
    required_fields = ["Title", "Author", "Book Id", "Exclusive Shelf", "Date Read"]

    try:
        with open(file_path, mode='r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            
            # Validate required columns exist
            if not reader.fieldnames:
                logger.error("CSV file appears to be empty or has no headers.")
                raise ValueError("CSV file appears to be empty or has no headers.")

            missing_columns = [col for col in required_fields if col not in reader.fieldnames]
            if missing_columns:
                logger.error(f"Missing required columns in CSV: {missing_columns}")
                raise ValueError(f"Missing required columns in CSV: {missing_columns}")
            

            for row in reader:
                # Extract required fields
                title = row.get("Title", "").strip()
                author = row.get("Author", "").strip()
                goodreads_id = row.get("Book Id", "").strip()
                status = row.get("Exclusive Shelf", "to-read").strip()
                finish_date = row.get("Date Read", "").strip()
                if not finish_date:
                    finish_date = None
                else:
                    try:
                        # Parse the date string to date object
                        finish_date = datetime.strptime(finish_date, "%Y/%m/%d").date()
                    except ValueError:
                        logger.warning(f"Invalid date format in Date Read: {finish_date}")
                        finish_date = None

                # Validate required fields
                if not goodreads_id:
                    logger.warning(f"Skipping row with no Goodreads ID: {row}")
                    continue
                if not title or not author:
                    logger.warning(f"Skipping row with missing title or author: {row}")
                    continue            

                book = {
                    "title": title,
                    "author": author,
                    "goodreads_id": goodreads_id,
                    "status": status,
                    "finish_date": finish_date
                }  

                books.append(book)
        
        return books

    except csv.Error as e:
        logger.error(f"Error parsing CSV file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing CSV file: {e}")
        raise


if __name__ == "__main__":
    from backend.app.config.logging_config import setup_logging
    setup_logging()

    test_csv_path = "test_data/goodreads_library_export.csv"
    test_books = parse_goodreads_csv(test_csv_path)
    print(test_books)