import pytest

REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
ME_URL = "/auth/me"

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "mypassword123"


# ── Register tests ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client):
    """A new user can register with valid email and password."""
    response = await client.post(REGISTER_URL, json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == TEST_EMAIL
    assert data["is_active"] is True
    assert "hashed_password" not in data # never expose this


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Registering with an already used email returns 400."""
    await client.post(REGISTER_URL, json={
        "email": TEST_EMAIL,
        "password" : TEST_PASSWORD,
    })
    # Try registering again with same email
    response = await client.post(REGISTER_URL, json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    """Registering with invalid email format returns 422."""
    response = await client.post(REGISTER_URL, json={
        "email": "not-an-email",
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 422
    # Pydantic rejects it before the route even runs
    # So we don't need below line
    # assert "invalid email format" in response.json()["detail"]


# ── Login tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client):
    """Registered user can login and receives a JWT token."""
    await client.post(REGISTER_URL, json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    response = await client.post(LOGIN_URL, json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Login with wrong password returns 401."""
    await client.post(REGISTER_URL, json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    response = await client.post(LOGIN_URL, json={
        "email": TEST_EMAIL,
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Login with email that was never registered returns 401."""
    response = await client.post(LOGIN_URL, json={
        "email": "nobody@example.com",
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 401

# ── Protected route tests ───────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_success(client):
    """Logged in user can access their profile."""
    await client.post(REGISTER_URL, json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    login = await client.post(LOGIN_URL, json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    token = login.json()["access_token"]

    response = await client.get(ME_URL, headers={
        "Authorization": f"Bearer {token}" 
    })
    assert response.status_code == 200
    assert response.json()["email"] == TEST_EMAIL


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    """Accessing protected route without token returns 403."""
    response = await client.get(ME_URL)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    """Accessing protected route with fake token returns 401."""
    response = await client.get(ME_URL, headers={
        "Authorization": "Bearer faketoken123"
    })
    assert response.status_code == 401