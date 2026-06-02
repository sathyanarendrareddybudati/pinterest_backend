import os
import sys
from unittest.mock import MagicMock, patch

os.environ["DATABASE_URL"] = "sqlite:///./test_temp.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ELASTICSEARCH_URL"] = "http://localhost:9200"
os.environ["ELASTICSEARCH_INDEX"] = "pins_test"
os.environ["ELASTICSEARCH_USERNAME"] = "test"
os.environ["ELASTICSEARCH_PASSWORD"] = "test"
os.environ["SECRET_KEY"] = "testsecretkeytestsecretkeytestsecretkey"
os.environ["ALGORITHM"] = "HS256"
os.environ["CLOUDINARY_CLOUD_NAME"] = "test"
os.environ["CLOUDINARY_API_KEY"] = "test"
os.environ["CLOUDINARY_API_SECRET"] = "test"

mock_es_client = MagicMock()
mock_es_client.indices.exists.return_value = True
mock_es_client.search.return_value = {"hits": {"hits": []}}
sys.modules['elasticsearch'] = MagicMock()
sys.modules['elasticsearch'].Elasticsearch = MagicMock(return_value=mock_es_client)

mock_redis_client = MagicMock()
sys.modules['redis'] = MagicMock()
sys.modules['redis'].Redis = MagicMock()
sys.modules['redis'].Redis.from_url = MagicMock(return_value=mock_redis_client)

mock_cloudinary = MagicMock()
mock_cloudinary.uploader.upload = MagicMock(
    return_value={"secure_url": "https://res.cloudinary.com/test/image/upload/v1/pins/test.jpg", "public_id": "pins/test"}
)
sys.modules['cloudinary'] = mock_cloudinary
sys.modules['cloudinary.uploader'] = mock_cloudinary.uploader

mock_torch = MagicMock()
mock_torch.unsqueeze = MagicMock()
mock_torch.no_grad = MagicMock()
sys.modules['torch'] = mock_torch

sys.modules['torchvision'] = MagicMock()
sys.modules['torchvision.models'] = MagicMock()
sys.modules['torchvision.transforms'] = MagicMock()

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from app.core.database import Base, engine, SessionLocal, get_db
from app.main import app as fastapi_app
import app.services.search_service
import app.services.trending
import app.services.recommendation
from app.services.visual_search import visual_search
import app.controllers.search
import app.controllers.pins
import app.controllers.feed

visual_search.encode_image = MagicMock(return_value=[0.1] * 2048)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_temp.db"):
        try:
            os.remove("test_temp.db")
        except Exception:
            pass

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(autouse=True)
def clean_db(db):
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()

@pytest.fixture(autouse=True)
def override_db(db):
    def _get_db_override():
        try:
            yield db
        finally:
            pass
    fastapi_app.dependency_overrides[get_db] = _get_db_override
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def client():
    with TestClient(fastapi_app) as c:
        yield c

@pytest.fixture(autouse=True)
def mock_services(monkeypatch):
    mock_search = MagicMock(return_value=[])
    mock_index = MagicMock()
    monkeypatch.setattr(app.services.search_service, "search_pins", mock_search)
    monkeypatch.setattr(app.services.search_service, "index_pin", mock_index)

    monkeypatch.setattr(app.controllers.search, "search_pins", mock_search)
    monkeypatch.setattr(app.controllers.pins, "index_pin", mock_index)

    mock_record_save = MagicMock()
    mock_trending_pins = MagicMock(return_value=[])
    monkeypatch.setattr(app.services.trending, "record_pin_save", mock_record_save)
    monkeypatch.setattr(app.services.trending, "get_trending_pins", mock_trending_pins)
    
    monkeypatch.setattr(app.controllers.feed, "get_trending_pins", mock_trending_pins)

    mock_recommend = MagicMock(return_value=[])
    mock_train = MagicMock()
    monkeypatch.setattr(app.services.recommendation.recommender, "recommend", mock_recommend)
    monkeypatch.setattr(app.services.recommendation.recommender, "train", mock_train)

    return {
        "search_pins": mock_search,
        "index_pin": mock_index,
        "record_pin_save": mock_record_save,
        "get_trending_pins": mock_trending_pins,
        "recommend": mock_recommend,
        "train": mock_train
    }
