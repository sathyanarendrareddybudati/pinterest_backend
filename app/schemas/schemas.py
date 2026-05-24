from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    class Config:
        from_attributes = True

class PinBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class PinCreate(PinBase):
    # Image will be uploaded via form data, creating an image_url
    pass

class PinResponse(PinBase):
    id: UUID
    image_url: str
    user_id: UUID
    save_count: int
    view_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class BoardBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_private: bool = False

class BoardResponse(BoardBase):
    id: UUID
    user_id: UUID
    cover_url: Optional[str] = None
    pin_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True
