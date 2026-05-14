import pytest 
from unittest.mock import patch, AsyncMock

SCAN_URL = "/scan"
RESULTS_URL = "/results"

# Fake scan result - we mock the actual HTTP fetch
# so tests don't hit the real internet
MOCK_SCAN_RESULT = {
    "url": "https://example.com",
    "status_code" : 200,
    "page_title" : "Example Domain",
    "response_headers": {"server" : "ECS", "content-type": "text/html"},
    "technologies" : ["Netlify"],
    "error": None,
}


# ── Scan tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scan_success(client):
    """Submitting a valid URL returns scan results."""
    with patch(
        "app.main.fetch_url_details",
        new_callable=AsyncMock,
        return_value=MOCK_SCAN_RESULT,
    ):
        response = await client.post(SCAN_URL, json={
            "url": "https://example.com"
        })
    
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com"
    assert data["status_code"] == 200
    assert data["page_title"] == "Example Domain"
    assert data["from_cache"] is False


@pytest.mark.asyncio
async def test_scan_invalid_url(client):
    """Submitting an invalid URL returns 422 validation error."""
    response = await client.post(SCAN_URL, json={
        "url": "not-a-url"
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_scan_second_request_is_cached(client):
    """Scanning the same URL twice returns from_cache=True"""
    with patch(
        "app.main.fetch_url_details",
        new_callable=AsyncMock,
        return_value=MOCK_SCAN_RESULT,
    ):
        # First scan - live fetch
        first = await client.post(SCAN_URL, json={
            "url": "https://example.com"
        })
        assert first.json()["from_cache"] is False

        # Second scan - should hit cache
        second = await client.post(SCAN_URL, json={
            "url": "https://example.com"
        })
        assert second.json()["from_cache"] is True


@pytest.mark.asyncio
async def test_scan_error_url(client):
    """If fetch fails, error is stored and returned."""
    error_result = {
        "url": "https://doesnotexist.xyz",
        "status_code": None,
        "page_title": None,
        "response_headers": None,
        "technologies": None,
        "error": "Network error: connection refused",
    }
    
    with patch(
        "app.main.fetch_url_details",
        new_callable=AsyncMock,
        return_value=error_result,
    ):
        response = await client.post(SCAN_URL, json={
            "url": "https://doesnotexist.xyz"
        })

    assert response.status_code == 201
    data = response.json()
    assert data["error"] is not None
    assert data["status_code"] is None


# ── Results tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_results_empty(client):
    """List results returns empty list when no scans done."""
    response = await client.get(RESULTS_URL)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_results_after_scan(client):
    """List results returns scans after one is done."""
    with patch(
        "app.main.fetch_url_details",
        new_callable=AsyncMock,
        return_value=MOCK_SCAN_RESULT,
    ):
        await client.post(SCAN_URL, json={
            "url": "https://example.com"
        })
    
    response = await client.get(RESULTS_URL)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_single_result(client):
    """Fetching a specific scan by ID returns full details."""
    with patch(
        "app.main.fetch_url_details",
        new_callable=AsyncMock,
        return_value=MOCK_SCAN_RESULT,
    ):
        scan = await client.post(SCAN_URL, json={
            "url": "https://example.com"
        })
    
    scan_id = scan.json()["id"]
    response = await client.get(f"{RESULTS_URL}/{scan_id}")
    assert response.status_code == 200
    assert response.json()["id"] == scan_id


@pytest.mark.asyncio
async def test_get_nonexistent_result(client):
    """Fetching a scan ID that doesn't exist returns 404."""
    response = await client.get(f"{RESULTS_URL}/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_refetch_url(client):
    """Refetching a URL creates a new record with from_cache=False"""
    with patch(
        "app.main.fetch_url_details",
        new_callable=AsyncMock,
        return_value=MOCK_SCAN_RESULT,
    ):
        # Initial Scan
        scan = await client.post(SCAN_URL, json={
            "url": "https://example.com"
        })
        scan_id = scan.json()["id"]

        # Refetch
        response = await client.post(f"{RESULTS_URL}/{scan_id}/refetch")

    assert response.status_code == 201
    assert response.json()["from_cache"] is False
    # New record created - different ID
    assert response.json()["id"] != scan_id