import uuid
from uuid import UUID
from PIL import Image
from io import BytesIO

def get_test_image_bytes():
    img = Image.new('RGB', (10, 10), color='red')
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

TINY_PNG = get_test_image_bytes()

def test_create_pin_unauthorized(client):
    files = {"file": ("test.png", TINY_PNG, "image/png")}
    data = {"title": "Test Title", "description": "Test Description"}
    response = client.post("/api/pins/", files=files, data=data)
    assert response.status_code == 401

def test_create_and_get_pin_success(client):
    register_payload = {
        "username": "pinuser",
        "email": "pinuser@example.com",
        "password": "pinpassword123"
    }
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 200
    user_id = response.json()["id"]

    login_data = {
        "username": "pinuser",
        "password": "pinpassword123"
    }
    response = client.post("/api/auth/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("test.png", TINY_PNG, "image/png")}
    data = {"title": "Beautiful Sunset", "description": "A very beautiful sunset view."}
    response = client.post("/api/pins/", headers=headers, files=files, data=data)
    assert response.status_code == 200
    
    pin_data = response.json()
    assert pin_data["title"] == "Beautiful Sunset"
    assert pin_data["description"] == "A very beautiful sunset view."
    assert "id" in pin_data
    assert pin_data["user_id"] == user_id
    assert "image_url" in pin_data
    
    pin_id = pin_data["id"]

    response = client.get(f"/api/pins/{pin_id}")
    assert response.status_code == 200
    get_data = response.json()
    assert get_data["id"] == pin_id
    assert get_data["title"] == "Beautiful Sunset"

def test_get_pin_not_found(client):
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/api/pins/{random_uuid}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Pin not found"
