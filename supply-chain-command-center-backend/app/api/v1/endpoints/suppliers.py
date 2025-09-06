from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database

router = APIRouter()

@router.get("/")
async def get_suppliers(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all suppliers"""
    return {"message": "Supplier endpoints - to be implemented"}

@router.post("/")
async def create_supplier(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create new supplier"""
    return {"message": "Create supplier endpoint - to be implemented"}
