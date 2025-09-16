from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()


@router.get("/")
async def get_users(db: AsyncSession = Depends(get_db)):
    """Get all users"""
    return {"users": []}


@router.post("/")
async def create_user(db: AsyncSession = Depends(get_db)):
    """Create a new user"""
    return {"message": "User created"}


@router.get("/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID"""
    return {"user_id": user_id}
