from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.config import settings
from app.database import get_db, init_db
from app.models import ScanResult
from app.schemas import ScanRequest, ScanResultResponse, ScanResultSummary
from app.services import fetch_url_details
from app.cache import get_cached_result, set_cached_result, invalidate_cache, close_redis
from app.auth.router import router as auth_router

# App Creation - FastAPI Application
app = FastAPI(
    title="URL Scanner",
    description="Submit URLs to scan their headers, title, status, and tech stacks.",
    version="1.0.0",
)

app.include_router(auth_router)

# ── Lifecycle ─────────────────────────────────────────

# Server Starts
@app.on_event("startup")
async def startup():
    await init_db()

# Server Shutdown
@app.on_event("shutdown")
async def shutdown():
    await close_redis()

# ── Routes ─────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/scan", response_model=ScanResultResponse, status_code=201)
async def scan_url(
    body: ScanRequest,
    db: AsyncSession = Depends(get_db),
):
    url = str(body.url)

    #1. Check cache first
    cached = await get_cached_result(url)
    if cached:
        record = ScanResult(
            url=cached["url"],
            status_code=cached.get("status_code"),
            page_title=cached.get("page_title"),
            response_headers=cached.get("response_headers"),
            technologies=cached.get("technologies"),
            error=cached.get("error"),
            from_cache=True,
        )
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record
    
    #2. Live Fetch
    details = await fetch_url_details(url)

    #3. Save to DB
    record = ScanResult(
        url=details["url"],
        status_code=details.get("status_code"),
        page_title=details.get("page_title"),
        response_headers=details.get("response_headers"),
        technologies=details.get("technologies"),
        error=details.get("error"),
        from_cache=False,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    #4. Cache result if no error
    if not details.get("error"):
        await set_cached_result(url, details)
    
    return record

@app.get("/results", response_model=list[ScanResultSummary])
async def list_results(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ScanResult)
        .order_by(desc(ScanResult.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@app.get("/results/{scan_id}", response_model=ScanResultResponse)
async def get_result(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
):
    record = await db.get(ScanResult, scan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scan result not found")
    return record

@app.post("/results/{scan_id}/refetch", response_model=ScanResultResponse, status_code=201)
async def refetch_url(
    scan_id: int,
    db: AsyncSession = Depends(get_db)
):
    original = await db.get(ScanResult, scan_id)
    if not original:
        raise HTTPException(status_code=404, detail="Scan result not found")
    
    url = original.url
    await invalidate_cache(url)
    details = await fetch_url_details(url)

    # Save new record — exclude id and created_at so DB generates them
    new_record = ScanResult(
        url=details["url"],
        status_code=details.get("status_code"),
        page_title=details.get("page_title"),
        response_headers=details.get("response_headers"),
        technologies=details.get("technologies"),
        error=details.get("error"),
        from_cache=False,
    )
    db.add(new_record)
    await db.flush()
    await db.refresh(new_record)

    if not details.get("error"):
        await set_cached_result(url, details)
    
    return new_record

