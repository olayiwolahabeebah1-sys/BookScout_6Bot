import requests

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
GUTENDEX_URL = "https://gutendex.com/books"


def search_google_books(query: str, max_results: int = 5):
    """Search Google Books for metadata, covers, and descriptions."""
    params = {"q": query, "maxResults": max_results}
    resp = requests.get(GOOGLE_BOOKS_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        results.append({
            "id": item.get("id"),
            "title": info.get("title", "Unknown title"),
            "authors": ", ".join(info.get("authors", [])) or "Unknown author",
            "description": info.get("description", "No description available."),
            "thumbnail": info.get("imageLinks", {}).get("thumbnail"),
            "info_link": info.get("infoLink"),
            "published": info.get("publishedDate", "N/A"),
        })
    return results


def search_gutenberg(query: str, max_results: int = 5):
    """Search Project Gutenberg for free, public-domain full texts."""
    params = {"search": query}
    resp = requests.get(GUTENDEX_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("results", [])[:max_results]:
        formats = item.get("formats", {})
        download_url = (
            formats.get("application/epub+zip")
            or formats.get("text/plain; charset=utf-8")
            or formats.get("text/plain")
        )
        results.append({
            "id": item.get("id"),
            "title": item.get("title", "Unknown title"),
            "authors": ", ".join(a["name"] for a in item.get("authors", [])) or "Unknown author",
            "download_url": download_url,
        })
    return results
