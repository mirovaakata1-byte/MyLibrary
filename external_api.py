import requests
from typing import Optional, Dict, Any

OPEN_LIBRARY_API_URL = "https://openlibrary.org/api/books"
OPEN_LIBRARY_COVERS_URL = "https://covers.openlibrary.org/b"


def search_by_isbn(isbn: str) -> Optional[Dict[str, Any]]:
    """Ищет книгу по ISBN в Open Library API и возвращает структурированные данные."""
    params = {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"}

    try:
        response = requests.get(OPEN_LIBRARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    key = f"ISBN:{isbn}"
    book_data = data.get(key)
    if not book_data:
        return None

    authors_list = book_data.get("authors", [])
    authors = [a.get("name") for a in authors_list]

    publishers_list = book_data.get("publishers", [])
    publisher = publishers_list[0].get("name") if publishers_list else None

    publish_date = book_data.get("publish_date")
    year = None
    if publish_date:
        import re
        match = re.match(r"(\d{4})", publish_date)
        if match:
            year = int(match.group(1))

    description = book_data.get("notes") or book_data.get("description")

    # URL обложки (Open Library Covers API)
    cover_id = None
    if book_data.get("cover"):
        cover_id = book_data["cover"].get("large") or book_data["cover"].get("medium") or book_data["cover"].get(
            "small")
    cover_url = f"{OPEN_LIBRARY_COVERS_URL}/id/{cover_id}-L.jpg" if cover_id else None

    return {
        "isbn": isbn,
        "title": book_data.get("title"),
        "authors": authors,
        "publisher": publisher,
        "year": year,
        "pages": book_data.get("number_of_pages"),
        "description": description,
        "cover_url": cover_url,
    }