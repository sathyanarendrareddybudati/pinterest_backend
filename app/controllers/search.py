from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Pin
from app.schemas.schemas import PinResponse
from typing import List, Optional
from app.services.search_service import search_pins

router = APIRouter()


@router.get("/", response_model=List[PinResponse])
def search(
    query: str = Query(...), limit: int = Query(10), db: Session = Depends(get_db)
):
    """
    Text-based search utilizing Elasticsearch BM25 (keyword).
    """
    pin_ids = search_pins(query=query, size=limit)
    if not pin_ids:
        return []

    from uuid import UUID
    valid_ids = []
    for pid in pin_ids:
        try:
            valid_ids.append(UUID(str(pid)))
        except (ValueError, TypeError):
            continue

    pins = db.query(Pin).filter(Pin.id.in_(valid_ids)).all()
    return pins


@router.post("/visual", response_model=List[PinResponse])
async def visual_search_endpoint(
    file: UploadFile = File(...), limit: int = Query(10), db: Session = Depends(get_db)
):
    """
    Image similarity search utilizing ResNet50 visual embeddings and Elasticsearch Vector search.
    """
    image_bytes = await file.read()

    # Validate image
    from PIL import Image, UnidentifiedImageError
    from io import BytesIO

    try:
        img = Image.open(BytesIO(image_bytes))
        img.verify()  # Check if image is valid
    except (UnidentifiedImageError, Exception):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400, detail="Uploaded file is not a valid image."
        )

    from app.services.visual_search import visual_search
    query_vector = visual_search.encode_image(image_bytes)

    # Hybrid search (vector only here)
    pin_ids = search_pins(query=None, query_vector=query_vector, size=limit)

    if not pin_ids:
        return []

    from uuid import UUID
    valid_ids = []
    for pid in pin_ids:
        try:
            valid_ids.append(UUID(str(pid)))
        except (ValueError, TypeError):
            continue

    pins = db.query(Pin).filter(Pin.id.in_(valid_ids)).all()
    return pins
