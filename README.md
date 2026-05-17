<div align="center">

# 🔍 URL Scanner API

### A high-performance backend service that scans URLs and extracts page titles, HTTP headers, status codes, and detected technologies.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-18%20Passing-brightgreen?style=for-the-badge&logo=pytest)](https://pytest.org)

[Features](#-features) • [Tech Stack](#-tech-stack) • [Quick Start](#-quick-start) • [API Endpoints](#-api-endpoints) • [Project Structure](#-project-structure) • [Testing](#-testing)

</div>

---

## ✨ Features

- 🌐 **URL Scanning** — Submit any URL and get back page title, HTTP headers, status code, and detected technologies
- ⚡ **Redis Caching** — Results cached for 1 hour. Same URL scanned twice returns instantly with `from_cache: true`
- 🔄 **Refetch** — Force a fresh scan on any previously scanned URL, busting the cache automatically
- 📜 **Scan History** — All results saved to PostgreSQL. View, paginate, and filter past scans
- 🔐 **JWT Authentication** — Register, login, and protect routes with Bearer token auth
- 🛠️ **Tech Detection** — Detects frameworks, CDNs, analytics tools, CMS platforms from headers and HTML
- 🧪 **18 Tests** — Full test suite covering auth and scan endpoints with mocked Redis and SQLite
- 🐳 **Docker Compose** — One command to spin up the entire stack

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | FastAPI + Uvicorn |
| **Database** | PostgreSQL 16 + SQLAlchemy (async) |
| **Cache** | Redis 7 |
| **Auth** | JWT (python-jose) + bcrypt |
| **HTTP Client** | httpx (async) |
| **HTML Parsing** | BeautifulSoup4 |
| **Tech Detection** | builtwith + custom header/HTML fingerprinting |
| **Testing** | pytest + pytest-asyncio + SQLite + MockRedis |
| **Containerization** | Docker + Docker Compose |

---

## 🚀 Quick Start

### Option 1 — Docker Compose (Recommended)

> One command starts PostgreSQL, Redis, and the API together.

```bash
# Clone the repo
git clone https://github.com/your-username/url-scanner.git
cd url-scanner

# Copy environment file
cp .env.example .env

# Start everything
docker-compose up --build
```

API is live at → **http://localhost:8000**
Swagger UI at → **http://localhost:8000/docs**

---

### Option 2 — Run Locally

**Prerequisites:** Python 3.11, PostgreSQL, Redis

```bash
# Clone and enter project
git clone https://github.com/your-username/url-scanner.git
cd url-scanner

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your DB and Redis credentials

# Start the server
uvicorn app.main:app --reload
```

---

## ⚙️ Environment Variables

Create a `.env` file in the root folder (copy from `.env.example`):

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/urlscanner
REDIS_URL=redis://localhost:6379
CACHE_TTL_SECONDS=3600
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> ⚠️ Never commit your `.env` file. It's already in `.gitignore`.

---

## 📡 API Endpoints

### 🔍 Scanning

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/scan` | Submit a URL to scan |
| `GET` | `/results` | List all past scans (paginated) |
| `GET` | `/results/{id}` | Get full details of one scan |
| `POST` | `/results/{id}/refetch` | Re-scan a URL, busting cache |
| `GET` | `/health` | Server health check |

### 🔐 Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create a new account |
| `POST` | `/auth/login` | Login and receive JWT token |
| `GET` | `/auth/me` | Get current user profile (protected) |

---

## 📖 Usage Examples

### Register and Login

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "mypassword123"}'

# Login — returns access_token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "mypassword123"}'
```

### Scan a URL

```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

**Response:**
```json
{
  "id": 1,
  "url": "https://example.com/",
  "status_code": 200,
  "page_title": "Example Domain",
  "response_headers": {
    "content-type": "text/html; charset=UTF-8",
    "server": "ECS"
  },
  "technologies": ["Google Fonts", "Netlify"],
  "from_cache": false,
  "error": null,
  "created_at": "2026-05-07T23:30:45.584475"
}
```

### Scan same URL again — cache hit

```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Response will have:
# "from_cache": true  ← returned instantly from Redis
```

### List past scans with pagination

```bash
curl "http://localhost:8000/results?limit=10&offset=0"
```

### Refetch — force fresh scan

```bash
curl -X POST http://localhost:8000/results/1/refetch
```

---

## 🗂️ Project Structure

```
url-scanner/
├── app/
│   ├── main.py          # FastAPI app + all routes
│   ├── config.py        # Settings loaded from .env
│   ├── database.py      # Async DB engine + session management
│   ├── models.py        # SQLAlchemy ORM — scan_results table
│   ├── schemas.py       # Pydantic request/response validation
│   ├── services.py      # URL fetch + HTML parse + tech detection
│   ├── cache.py         # Redis get/set/invalidate helpers
│   └── auth/
│       ├── models.py    # Users table
│       ├── schemas.py   # Auth request/response shapes
│       ├── router.py    # Register, login, /me endpoints
│       └── utils.py     # Password hashing + JWT creation
├── tests/
│   ├── conftest.py      # Test DB, MockRedis, client fixture
│   ├── test_auth.py     # 9 auth tests
│   └── test_scan.py     # 9 scan tests
├── .env.example         # Environment variable template
├── .gitignore           # Ignores venv, .env, __pycache__
├── Dockerfile           # Container build instructions
├── docker-compose.yml   # Full stack orchestration
├── pytest.ini           # Pytest async configuration
└── requirements.txt     # All Python dependencies
```

---

## 🧪 Testing

The test suite runs with a SQLite test database and an in-memory MockRedis — no Docker or internet required.

```bash
# Run all tests
pytest tests/ -v

# Run only auth tests
pytest tests/test_auth.py -v

# Run only scan tests
pytest tests/test_scan.py -v
```

**Expected output:**
```
tests/test_auth.py::test_register_success            PASSED
tests/test_auth.py::test_register_duplicate_email    PASSED
tests/test_auth.py::test_register_invalid_email      PASSED
tests/test_auth.py::test_login_success               PASSED
tests/test_auth.py::test_login_wrong_password        PASSED
tests/test_auth.py::test_login_nonexistent_user      PASSED
tests/test_auth.py::test_get_me_success              PASSED
tests/test_auth.py::test_get_me_no_token             PASSED
tests/test_auth.py::test_get_me_invalid_token        PASSED
tests/test_scan.py::test_scan_success                PASSED
tests/test_scan.py::test_scan_invalid_url            PASSED
tests/test_scan.py::test_scan_second_request_cached  PASSED
tests/test_scan.py::test_scan_error_url              PASSED
tests/test_scan.py::test_list_results_empty          PASSED
tests/test_scan.py::test_list_results_after_scan     PASSED
tests/test_scan.py::test_get_single_result           PASSED
tests/test_scan.py::test_get_nonexistent_result      PASSED
tests/test_scan.py::test_refetch_url                 PASSED

18 passed in 4.2s ✅
```

---

## 🏗️ Architecture

```
Client (Browser / Postman)
          │
          ▼
    FastAPI App (port 8000)
    ┌─────────────────────────────────────┐
    │  POST /scan      → submit URL       │
    │  GET  /results   → list history     │
    │  GET  /results/{id} → one result   │
    │  POST /results/{id}/refetch         │
    │  POST /auth/register                │
    │  POST /auth/login                   │
    └──────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   Redis Cache           PostgreSQL
 (TTL: 1 hour)        (permanent store)
        │
        ▼
   httpx + BeautifulSoup + builtwith
   (async URL fetch + HTML parse + tech detect)
```

**Caching strategy:**
```
POST /scan arrives
      ↓
Check Redis → HIT  → return cached result instantly (from_cache: true)
      ↓ MISS
Fetch URL live (httpx)
      ↓
Save to PostgreSQL
      ↓
Store in Redis (TTL: 1 hour)
      ↓
Return result (from_cache: false)
```

---

## 🔐 Authentication Flow

```
POST /auth/register → hash password (bcrypt) → save to DB → return user
POST /auth/login    → verify password → create JWT → return token
GET  /auth/me       → validate JWT → return user profile
```

Protected routes use `Authorization: Bearer <token>` header.

---

## 📝 Design Decisions

- **Async throughout** — FastAPI + asyncpg + httpx are all async. No thread blocking on DB or HTTP operations
- **Refetch creates new record** — history is preserved. You can see how a page changed over time
- **Errors stored, never cached** — failed scans are saved to DB for visibility but never cached so retries always fetch fresh
- **Cache-aside pattern** — check cache first, miss → fetch → store → return
- **MockRedis in tests** — no Redis container needed to run tests. Fast and self-contained
- **SQLite in tests** — no PostgreSQL container needed either. Tests run anywhere

---

<div align="center">

Built with ❤️ using FastAPI · PostgreSQL · Redis · Docker

</div>
