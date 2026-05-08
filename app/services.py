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

    # ── 2. Server detection from headers ─────────────────────────────
    server = headers.get("server", "").lower()
    if "netlify" in server:
        technologies.add("Netlify")
    if "nginx" in server:
        technologies.add("Nginx")
    if "apache" in server:
        technologies.add("Apache")
    if "cloudflare" in server:
        technologies.add("Cloudflare")
    if "vercel" in server:
        technologies.add("Vercel")
    if "github" in server:
        technologies.add("GitHub Pages")
    if "awselb" in server or "aws" in server:
        technologies.add("Amazon AWS")
    if "microsoft" in server or "iis" in server:
        technologies.add("Microsoft IIS")
    if "openresty" in server:
        technologies.add("OpenResty")
    if "caddy" in server:
        technologies.add("Caddy")
    
    # ── 3. CDN and hosting from headers ───────────────────────────────
    via = headers.get("via", "").lower()
    if "cloudflare" in via:
        technologies.add("Cloudflare")
    if "varnish" in via:
        technologies.add("Varnish")

    x_powered = headers.get("x-powered-by", "").lower()
    if "php" in x_powered:
        technologies.add("PHP")
    if "express" in x_powered:
        technologies.add("Express.js")
    if "next.js" in x_powered:
        technologies.add("Next.js")
    if "asp.net" in x_powered:
        technologies.add("ASP.NET")

    if "x-vercel-id" in headers:
        technologies.add("Vercel")
    if "x-amz-cf-id" in headers or "x-amz-request-id" in headers:
        technologies.add("Amazon CloudFront")
    if "x-nf-request-id" in headers:
        technologies.add("Netlify")
    if "cf-ray" in headers:
        technologies.add("Cloudflare")
    if "x-github-request-id" in headers:
        technologies.add("GitHub Pages")
    if "x-shopify-stage" in headers or "x-shopid" in headers:
        technologies.add("Shopify")
    if "x-wp-total" in headers or "x-wp-totalpages" in headers:
        technologies.add("WordPress")

    # Cache and CDN headers
    if "x-cache" in headers:
        val = headers["x-cache"].lower()
        if "cloudfront" in val:
            technologies.add("Amazon CloudFront")

    # ── 4. HTML based detection ───────────────────────────
    html_lower = html.lower()

    # JavaScript frameworks
    if "react" in html_lower and ("react.development" in html_lower or
    "react.production" in html_lower or "_reactfiber" in html_lower or
    "data-reactroot" in html_lower or "__next" in html_lower):
        technologies.add("React")
    if "__next" in html_lower or "_next/static" in html_lower:
        technologies.add("Next.js")
    if "vue.js" in html_lower or "vue.min.js" in html_lower or "__vue__" in html_lower:
        technologies.add("Vue.js")
    if "angular" in html_lower and "ng-version" in html_lower:
        technologies.add("Angular")
    if "svelte" in html_lower and "__svelte" in html_lower:
        technologies.add("Svelte")
    if "gatsby" in html_lower and "gatsby-" in html_lower:
        technologies.add("Gatsby")

    # CSS frameworks
    if "bootstrap" in html_lower:
        technologies.add("Bootstrap")
    if "tailwind" in html_lower:
        technologies.add("Tailwind CSS")
    if "bulma" in html_lower:
        technologies.add("Bulma")
    if "materialize" in html_lower:
        technologies.add("Materialize CSS")
    if "foundation" in html_lower:
        technologies.add("Foundation")
    
    # Analytics & tracking
    if "google-analytics.com" in html_lower or "gtag(" in html_lower or "ga.js" in html_lower:
        technologies.add("Google Analytics")
    if "googletagmanager.com" in html_lower:
        technologies.add("Google Tag Manager")
    if "hotjar" in html_lower:
        technologies.add("Hotjar")
    if "segment.com" in html_lower or "segment.io" in html_lower:
        technologies.add("Segment")
    if "mixpanel" in html_lower:
        technologies.add("Mixpanel")
    if "clarity.ms" in html_lower:
        technologies.add("Microsoft Clarity")
    if "intercom" in html_lower:
        technologies.add("Intercom")
    if "crisp.chat" in html_lower:
        technologies.add("Crisp")
    if "tawk.to" in html_lower:
        technologies.add("Tawk.to")
    
    # CMS
    if "wp-content" in html_lower or "wp-includes" in html_lower:
        technologies.add("WordPress")
    if "drupal" in html_lower and "drupal.js" in html_lower:
        technologies.add("Drupal")
    if "joomla" in html_lower:
        technologies.add("Joomla")
    if "shopify" in html_lower and "cdn.shopify.com" in html_lower:
        technologies.add("Shopify")
    if "squarespace" in html_lower:
        technologies.add("Squarespace")
    if "wix.com" in html_lower:
        technologies.add("Wix")
    if "webflow" in html_lower:
        technologies.add("Webflow")
    
    # Font services
    if "fonts.googleapis.com" in html_lower:
        technologies.add("Google Fonts")
    if "fonts.typekit" in html_lower or "use.typekit" in html_lower:
        technologies.add("Adobe Fonts")
    
    # JavaScript libraries
    if "jquery" in html_lower:
        technologies.add("jQuery")
    if "lodash" in html_lower:
        technologies.add("Lodash")
    if "three.js" in html_lower or "three.min.js" in html_lower:
        technologies.add("Three.js")
    
    # Hosting platforms
    if "netlify" in html_lower:
        technologies.add("Netlify")
    if "vercel" in html_lower:
        technologies.add("Vercel")
    
    return sorted(list(technologies))

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