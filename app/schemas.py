from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict

# ── Request bodies ───────────────────────────────────────
class ScanRequest(BaseModel):
    url: HttpUrl

# ── Response bodies ───────────────────────────────────────
class ScanResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url:str
    status_code: int | None
    page_title: str| None
    response_headers: dict | None
    technologies: list | None
    from_cache: bool
    error: str | None
    created_at: datetime

class ScanResultSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    status_code: int | None
    page_title: str | None
    from_cache: bool
    error: str | None
    created_at: datetime
