def test_register_user_success(client):
    payload = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "strongpassword123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert "id" in data

def test_register_duplicate_username(client):
    payload = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "strongpassword123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200

    payload2 = {
        "username": "testuser",
        "email": "testuser2@example.com",
        "password": "anotherpassword"
    }
    response = client.post("/api/auth/register", json=payload2)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_login_success(client):
    payload = {
        "username": "loginuser",
        "email": "loginuser@example.com",
        "password": "correctpassword"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200

    login_data = {
        "username": "loginuser",
        "password": "correctpassword"
    }
    response = client.post("/api/auth/token", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    payload = {
        "username": "anotheruser",
        "email": "anotheruser@example.com",
        "password": "correctpassword"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200

    login_data = {
        "username": "anotheruser",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/token", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
