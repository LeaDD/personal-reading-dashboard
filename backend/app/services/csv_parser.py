import csv
import logging
import os
from pydantic import ValidationError
from datetime import datetime

from backend.app.schemas.books_schema import CSVBook

logger = logging.getLogger(__name__)

def parse_goodreads_csv(file_path: str) -> list[CSVBook]:
    """
    Parses a Goodreads CSV file and returns a list of books.

    Args:
        file_path (str): Path to the Goodreads CSV file.

    Returns:
        list[CSVBook]: List of CSVBook objects, each representing a book.
    """
    logger.info(f"Parsing Goodreads CSV file from {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"File {file_path} does not exist")
        raise FileNotFoundError(f"File {file_path} does not exist")

    # Check if the required columns are present in the CSV file
    required_columns = ["Title", "Author", "Book Id", "Exclusive Shelf", "Date Read"]


    books = []
    try:
        # Open the CSV file and read the data
        with open(file_path, mode='r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            # Check if the required columns are present in the CSV file
            for column in required_columns:
                if column not in reader.fieldnames:
                    logger.error(f"Column {column} not found in CSV file")
                    raise ValueError(f"Column {column} not found in CSV file")
            
            # Parse the data into CSVBook objects
            for row in reader:
                # Map the CSV column names to the CSVBook object fields

                try:
                    finish_date_str = row.get("Date Read").strip() or None

                    # Parse the ISBN-10 value
                    isbn_value = row.get("ISBN", "").strip()
                    if isbn_value:
                        isbn_value = isbn_value.replace('="', '').rstrip('"')
                        isbn_10 = isbn_value
                    else:
                        isbn_10 = None

                    # Parse the ISBN-13 value
                    isbn_13_value = row.get("ISBN13", "").strip()
                    if isbn_13_value:
                        isbn_13_value = isbn_13_value.replace('="', '').rstrip('"')
                        isbn_13 = isbn_13_value
                    else:
                        isbn_13 = None

                    # Parse the number of pages
                    num_pages_str = row.get("Number of Pages", "").strip()
                    num_pages = int(num_pages_str) if num_pages_str and num_pages_str.isdigit() else None

                    book_dict = {
                        "title": row.get("Title").strip(),
                        "author": row.get("Author").strip(),
                        "isbn_10":  isbn_10,
                        "isbn_13": isbn_13,
                        "additional_authors": row.get("Additional Authors").strip() if row.get("Additional Authors") else None,
                        "num_pages": num_pages,
                        "goodreads_id": row.get("Book Id").strip(),
                        "status": row.get("Exclusive Shelf").strip(),
                        "finish_date": datetime.strptime(finish_date_str, "%Y/%m/%d").date() if finish_date_str else None
                    }
                    books.append(CSVBook(**book_dict))
                except ValidationError as e:
                    logger.warning(f"Skipping invalid row: {e}")
                    continue
            
            logger.info(f"Parsed {len(books)} books from {file_path}")
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