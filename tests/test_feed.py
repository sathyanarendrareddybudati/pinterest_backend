import uuid
from app.models.models import Pin, User

def test_trigger_training(client):
    response = client.post("/api/feed/train-model")
    assert response.status_code == 200
    assert response.json() == {"message": "Training started"}

def test_get_feed_fallback_to_recent(client, db):
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    pin = Pin(title="Recent Pin", description="desc", image_url="http://example.com/img.jpg", user_id=user.id)
    db.add(pin)
    db.commit()

    response = client.get("/api/feed/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Recent Pin"

def test_get_feed_personalized(client, db, mock_services):
    user = User(username="testuser2", email="test2@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    pin1 = Pin(title="Pin 1", description="desc", image_url="http://example.com/img1.jpg", user_id=user.id)
    pin2 = Pin(title="Pin 2", description="desc", image_url="http://example.com/img2.jpg", user_id=user.id)
    db.add_all([pin1, pin2])
    db.commit()
    db.refresh(pin1)
    db.refresh(pin2)

    mock_services["recommend"].return_value = [pin1.id]

    response = client.get(f"/api/feed/recommendations?user_id={user.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(pin1.id)
    assert data[0]["title"] == "Pin 1"

def test_get_feed_fallback_to_trending(client, db, mock_services):
    user = User(username="testuser3", email="test3@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    pin1 = Pin(title="Trending Pin", description="desc", image_url="http://example.com/img1.jpg", user_id=user.id)
    db.add(pin1)
    db.commit()
    db.refresh(pin1)

    mock_services["recommend"].return_value = []
    mock_services["get_trending_pins"].return_value = [str(pin1.id)]

    response = client.get(f"/api/feed/recommendations?user_id={user.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(pin1.id)
    assert data[0]["title"] == "Trending Pin"

def test_trending_feed_success(client, db, mock_services):
    user = User(username="testuser4", email="test4@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    pin1 = Pin(title="Trending 1", description="desc", image_url="http://example.com/img1.jpg", user_id=user.id)
    db.add(pin1)
    db.commit()
    db.refresh(pin1)

    mock_services["get_trending_pins"].return_value = [str(pin1.id)]

    response = client.get("/api/feed/trending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Trending 1"

def test_trending_feed_fallback(client, db, mock_services):
    user = User(username="testuser5", email="test5@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    pin1 = Pin(title="Recent Pin Only", description="desc", image_url="http://example.com/img1.jpg", user_id=user.id)
    db.add(pin1)
    db.commit()
    db.refresh(pin1)

    mock_services["get_trending_pins"].return_value = []

    response = client.get("/api/feed/trending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Recent Pin Only"
