import httpx
import builtwith
from bs4 import BeautifulSoup

def detect_technologies(url: str, headers: dict, html: str) -> list:
    """
    Detect technologies from HTTP headers and HTML content.
    Combines builtwith with our own header/HTML based detection.
    """
    technologies = set()

    # ── 1. builtwith (basic detection) ─────────────────────────────
    try:
        tech_data = builtwith.parse(url, html)
        for tech_list in tech_data.values():
            for tech in tech_list:
                technologies.add(tech)
    except Exception:
        pass

async def fetch_url_details(url: str) -> dict:
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
        ) as client:
            response = await client.get(url)

        # ── Parse page title ─────────────────────────────────────
        page_title = None
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")
            title_tag = soup.find("title")
            if title_tag:
                page_title = title_tag.get_text(strip=True)
        
        # ── Clean headers ───────────────────────────────────────
        headers = dict(response.headers)

        # ── Detect technologies ──────────────────────────────────
        technologies = detect_technologies(url, headers, response.text)

        return {
            "url": url,
            "status_code": response.status_code,
            "page_title": page_title,
            "response_headers": headers,
            "technologies": technologies,
            "error": None,
        }
    
    except httpx.TimeoutException:
        return {
            "url": url,
            "error": "Request timed out after 15 seconds",
            "status_code": None,
            "page_title": None,
            "response_headers": None,
            "technologies": None,
        }
    
    except httpx.RequestError as e:
        return {
            "url": url,
            "error": f"Network error: {str(e)}",
            "status_code": None,
            "page_title": None,
            "response_headers": None,
            "technologies": None,
        }