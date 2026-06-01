from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    HTTPException,
)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Pin, User, ImageMetadata
from app.schemas.schemas import PinResponse
from app.services.cloudinary_service import upload_image_to_cloudinary
from app.services.visual_search import visual_search
from app.services.search_service import index_pin
from app.core.config import settings
from typing import Optional
from uuid import UUID
import jwt

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Decode JWT token and return the authenticated user."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("id")
        if user_id is None:
            raise HTTPException(
                status_code=401, detail="Invalid token: missing user id"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def process_pin_background(
    pin_id: UUID, image_bytes: bytes, title: str, description: str
):
    """
    Background task to generate visual embeddings via ResNet50
    and index the pin inside Elasticsearch.
    """
    embedding = visual_search.encode_image(image_bytes)
    index_pin(pin_id, title, description, embedding)


@router.post("/", response_model=PinResponse)
async def create_pin(
    background_tasks: BackgroundTasks,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image_bytes = await file.read()

    # Upload image and get Cloudinary info
    from app.services import cloudinary_service

    upload_result = None
    try:
        upload_result = cloudinary_service.cloudinary.uploader.upload(
            image_bytes,
            public_id=None,
            overwrite=True,
            resource_type="image",
        )
        cloudinary_url = upload_result.get("secure_url")
        cloudinary_public_id = upload_result.get("public_id")
    except Exception:
        cloudinary_url = await upload_image_to_cloudinary(image_bytes, file.filename)
        cloudinary_public_id = None

    # Extract image metadata
    from PIL import Image
    from io import BytesIO

    try:
        image = Image.open(BytesIO(image_bytes))
        width, height = image.size
        aspect_ratio = width / height if height else None
        mime_type = Image.MIME.get(image.format)
        # Dominant color extraction
        small_img = image.copy()
        small_img.thumbnail((50, 50))
        result = small_img.convert("RGB").getcolors(50 * 50)
        dominant_color = max(result, key=lambda x: x[0])[1] if result else None
        if dominant_color:
            dominant_color = "#%02x%02x%02x" % dominant_color
        # Blurhash
        from blurhash import encode

        blur_hash = encode(image, x_components=4, y_components=3)
    except Exception:
        width = height = aspect_ratio = None
        mime_type = None
        dominant_color = None
        blur_hash = None
    file_size = len(image_bytes)

    # Save Pin
    new_pin = Pin(
        title=title,
        description=description,
        image_url=cloudinary_url,
        user_id=current_user.id,
    )
    db.add(new_pin)
    db.commit()
    db.refresh(new_pin)

    # Save ImageMetadata
    metadata = ImageMetadata(
        pin_id=new_pin.id,
        s3_key=cloudinary_public_id,
        mime_type=mime_type,
        width_px=width,
        height_px=height,
        aspect_ratio=aspect_ratio,
        file_size=file_size,
        dominant_color=dominant_color,
        blur_hash=blur_hash,
        cdn_url=cloudinary_url,
    )
    db.add(metadata)
    db.commit()

    background_tasks.add_task(
        process_pin_background, new_pin.id, image_bytes, title or "", description or ""
    )
    return new_pin


@router.get("/{pin_id}", response_model=PinResponse)
def get_pin(pin_id: UUID, db: Session = Depends(get_db)):
    pin = db.query(Pin).filter(Pin.id == pin_id).first()
    if not pin:
        raise HTTPException(status_code=404, detail="Pin not found")
    return pin
