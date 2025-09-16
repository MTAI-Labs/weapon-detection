from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()


@router.get("/")
async def get_items(db: AsyncSession = Depends(get_db)):
    """Get all items"""
    return {"items": []}


@router.post("/")
async def create_item(db: AsyncSession = Depends(get_db)):
    """Create a new item"""
    return {"message": "Item created"}


@router.get("/{item_id}")
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Get item by ID"""
    return {"item_id": item_id}
