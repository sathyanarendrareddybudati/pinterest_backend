import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Float, BigInteger, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    avatar_url = Column(String)
    bio = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    boards = relationship("Board", back_populates="user", cascade="all, delete-orphan")
    board_members = relationship("BoardMember", back_populates="user", cascade="all, delete-orphan")
    pins = relationship("Pin", back_populates="user", cascade="all, delete-orphan")
    saves = relationship("Save", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    pin_views = relationship("PinView", back_populates="user")
    notifications = relationship("Notification", foreign_keys="Notification.user_id", back_populates="user", cascade="all, delete-orphan")
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following", cascade="all, delete-orphan")
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, nullable=False)
    device_info = Column(String)
    ip_address = Column(String)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="sessions")

class Board(Base):
    __tablename__ = "boards"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    cover_url = Column(String)
    is_private = Column(Boolean, default=False)
    pin_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)
    
    user = relationship("User", back_populates="boards")
    members = relationship("BoardMember", back_populates="board", cascade="all, delete-orphan")
    saves = relationship("Save", back_populates="board", cascade="all, delete-orphan")

class BoardMember(Base):
    __tablename__ = "board_members"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(pgUUID(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False) # 'owner', 'editor', 'viewer'
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint("board_id", "user_id", name="uq_board_user"),
        CheckConstraint("role IN ('owner', 'editor', 'viewer')", name="chk_role")
    )
    
    board = relationship("Board", back_populates="members")
    user = relationship("User", back_populates="board_members")

class Pin(Base):
    __tablename__ = "pins"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String)
    description = Column(String)
    image_url = Column(String, nullable=False)
    image_key = Column(String)
    source_url = Column(String)
    save_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_pins_created_at', created_at.desc()),
    )
    
    user = relationship("User", back_populates="pins")
    metadata_rel = relationship("ImageMetadata", back_populates="pin", uselist=False, cascade="all, delete-orphan")
    saves = relationship("Save", back_populates="pin", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="pin", cascade="all, delete-orphan")
    views = relationship("PinView", back_populates="pin", cascade="all, delete-orphan")
    tags = relationship("PinTag", back_populates="pin", cascade="all, delete-orphan")

class ImageMetadata(Base):
    __tablename__ = "image_metadata"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pin_id = Column(pgUUID(as_uuid=True), ForeignKey("pins.id", ondelete="CASCADE"), unique=True, nullable=False)
    s3_key = Column(String)
    mime_type = Column(String)
    width_px = Column(Integer)
    height_px = Column(Integer)
    aspect_ratio = Column(Float)
    file_size = Column(BigInteger)
    dominant_color = Column(String)
    blur_hash = Column(String)
    cdn_url = Column(String)
    
    pin = relationship("Pin", back_populates="metadata_rel")

class Save(Base):
    __tablename__ = "saves"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pin_id = Column(pgUUID(as_uuid=True), ForeignKey("pins.id", ondelete="CASCADE"), nullable=False, index=True)
    board_id = Column(pgUUID(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    saved_at = Column(DateTime, server_default=func.now())
    note = Column(String)
    
    __table_args__ = (
        UniqueConstraint("user_id", "pin_id", "board_id", name="uq_save_user_pin_board"),
    )
    
    user = relationship("User", back_populates="saves")
    pin = relationship("Pin", back_populates="saves")
    board = relationship("Board", back_populates="saves")

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pin_id = Column(pgUUID(as_uuid=True), ForeignKey("pins.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(pgUUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), index=True)
    content = Column(String, nullable=False)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)
    
    user = relationship("User", back_populates="comments")
    pin = relationship("Pin", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", cascade="all, delete-orphan", back_populates="parent")

class CommentLike(Base):
    __tablename__ = "comment_likes"
    
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    comment_id = Column(pgUUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, server_default=func.now())

class PinView(Base):
    __tablename__ = "pin_views"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pin_id = Column(pgUUID(as_uuid=True), ForeignKey("pins.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    viewed_at = Column(DateTime, server_default=func.now())
    
    pin = relationship("Pin", back_populates="views")
    user = relationship("User", back_populates="pin_views")

class Follow(Base):
    __tablename__ = "follows"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    following_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follow_follower_following"),
        CheckConstraint("follower_id <> following_id", name="chk_no_self_follow")
    )
    
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    slug = Column(String, unique=True)
    normalized_name = Column(String)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    pins = relationship("PinTag", back_populates="tag", cascade="all, delete-orphan")

class PinTag(Base):
    __tablename__ = "pin_tags"
    
    pin_id = Column(pgUUID(as_uuid=True), ForeignKey("pins.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(pgUUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True)
    pinned_at = Column(DateTime, server_default=func.now())
    
    pin = relationship("Pin", back_populates="tags")
    tag = relationship("Tag", back_populates="pins")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    type = Column(String, nullable=False)
    entity_type = Column(String)
    entity_id = Column(pgUUID(as_uuid=True))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("type IN ('follow', 'save', 'comment', 'mention', 'board_invite')", name="chk_notification_type"),
        Index('idx_notifications_user_read', user_id, is_read)
    )
    
    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    actor = relationship("User", foreign_keys=[actor_id])
