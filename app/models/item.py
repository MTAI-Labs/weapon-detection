from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from .base import Base


class Item(Base):
    __tablename__ = "items"
    __allow_unmapped__ = True  # Allow legacy type annotations
    
    # Core item fields
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Pricing (using Numeric for precision)
    price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)  # ISO 4217
    
    # Status and categorization
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    category = Column(String(50), nullable=True, index=True)
    
    # PostgreSQL array for tags
    tags = Column(ARRAY(String(50)), default=list, nullable=False)
    
    # Flexible extra data storage
    extra_data = Column(JSONB, default=dict, nullable=False)
    
    # Foreign key to user
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Relationships
    owner = relationship("User", back_populates="items")
    
    # PostgreSQL specific indexes for performance
    __table_args__ = (
        Index('idx_items_title_active', 'title', 'is_active'),
        Index('idx_items_category_active', 'category', 'is_active'),
        Index('idx_items_owner_active', 'owner_id', 'is_active'),
        Index('idx_items_price_currency', 'price', 'currency'),
        Index('idx_items_created_at', 'created_at'),
        # GIN indexes for JSONB and array fields
        Index('idx_items_extra_data_gin', 'extra_data', postgresql_using='gin'),
        Index('idx_items_tags_gin', 'tags', postgresql_using='gin'),
    )
    
    @property
    def price_formatted(self) -> str:
        """Format price with currency"""
        if self.price is None:
            return "N/A"
        return f"{self.currency} {self.price:.2f}"
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the item"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the item"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def __repr__(self) -> str:
        return f"<Item(id={self.id}, title={self.title}, owner_id={self.owner_id})>"