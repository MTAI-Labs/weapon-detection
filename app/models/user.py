from sqlalchemy import Column, String, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

from .base import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"
    __allow_unmapped__ = True  # Allow legacy type annotations
    
    # Core user fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile fields
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Extra data - PostgreSQL JSONB for flexible storage
    extra_data = Column(JSONB, default=dict, nullable=False)
    
    # Relationships
    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")
    
    # PostgreSQL specific indexes for performance
    __table_args__ = (
        Index('idx_users_email_active', 'email', 'is_active'),
        Index('idx_users_username_active', 'username', 'is_active'),
        Index('idx_users_created_at', 'created_at'),
        # GIN index for JSONB extra_data field
        Index('idx_users_extra_data_gin', 'extra_data', postgresql_using='gin'),
    )
    
    def set_password(self, password: str) -> None:
        """Hash and set user password"""
        self.hashed_password = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password, self.hashed_password)
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is active and verified"""
        return self.is_active and self.is_verified
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"