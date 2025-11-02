import httpx
import logging

logger = logging.getLogger(__name__)

def get_google_books_data(title: str, author: str) -> dict | None:
    logger.info(f"Getting Google Books data for {title} by {author}")

    base_url = "https://www.googleapis.com/books/v1/volumes"

    query = f"intitle:{title}+inauthor:{author}"

    params = {
        "q": query,
        "maxResults": 5,
        "orderBy": "relevance"  # Sort by relevance
    }

    response = httpx.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()

        if data.get("items"):
            first_result = data["items"][0]
            volume_info = first_result.get("volumeInfo", {})     

            isbn_10 = None
            isbn_13 = None

            for identifier in volume_info.get("industryIdentifiers", []):
                if identifier.get("type") == "ISBN_10":
                    isbn_10 = identifier.get("identifier")
                elif identifier.get("type") == "ISBN_13":
                    isbn_13 = identifier.get("identifier")

            book = {
                "google_books_id": first_result.get("id"),
                "google_books_link": first_result.get("selfLink"),
                "title": volume_info.get("title"),
                "authors": volume_info.get("authors"),
                "published_date": volume_info.get("publishedDate"),
                "page_count": volume_info.get("pageCount"),
                "categories": volume_info.get("categories"),
                "genre": volume_info.get("categories")[0] if volume_info.get("categories") else None,
                "description": volume_info.get("description"),
                "isbn_10": isbn_10 if isbn_10 else None,
                "isbn_13": isbn_13 if isbn_13 else None
            }
            return book
        else: 
            logger.warning(f"No results found for {title} by {author}")
            return None
            
    else:
        logger.error(f"error: status code {response.status_code}")
        logger.error(response.text)
        return None

if __name__ == "__main__":
    # Test with a known book from user's CSV
    print("=== TEST 1: Restaurant at End of Universe ===\n")
    book1 = get_google_books_data("The Restaurant at the End of the Universe", "Douglas Adams")
    print(book1)
    
    # Test with another book to check for categories
    print("\n\n=== TEST 2: Testing for Categories ===\n")
    book2 = get_google_books_data("Dune", "Frank Herbert")       
    print(book2)


