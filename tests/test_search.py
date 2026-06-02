from app.models.models import Pin, User
from PIL import Image
from io import BytesIO

def get_test_image_bytes():
    img = Image.new('RGB', (10, 10), color='red')
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

TINY_PNG = get_test_image_bytes()

def test_text_search_no_results(client):
    response = client.get("/api/search/?query=nonexistent")
    assert response.status_code == 200
    assert response.json() == []

def test_text_search_success(client, db, mock_services):
    user = User(username="searchuser", email="search@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    pin = Pin(title="Cat Pic", description="A cute cat", image_url="http://example.com/cat.jpg", user_id=user.id)
    db.add(pin)
    db.commit()
    db.refresh(pin)

    mock_services["search_pins"].return_value = [str(pin.id)]

    response = client.get("/api/search/?query=cat")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Cat Pic"
    assert data[0]["id"] == str(pin.id)
    
    mock_services["search_pins"].assert_called_once_with(query="cat", size=10)

def test_visual_search_invalid_image(client):
    files = {"file": ("test.txt", b"this is not an image", "text/plain")}
    response = client.post("/api/search/visual", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is not a valid image."

def test_visual_search_success(client, db, mock_services):
    user = User(username="visualuser", email="visual@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    pin = Pin(title="Matching Pin", description="desc", image_url="http://example.com/match.jpg", user_id=user.id)
    db.add(pin)
    db.commit()
    db.refresh(pin)

    mock_services["search_pins"].return_value = [str(pin.id)]

    files = {"file": ("test.png", TINY_PNG, "image/png")}
    response = client.post("/api/search/visual", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Matching Pin"
    assert data[0]["id"] == str(pin.id)

    mock_services["search_pins"].assert_called_once_with(query=None, query_vector=[0.1] * 2048, size=10)
