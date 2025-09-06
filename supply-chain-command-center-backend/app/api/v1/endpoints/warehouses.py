from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database

router = APIRouter()

@router.get("/")
async def get_warehouses(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all warehouses"""
    return {"message": "Warehouse endpoints - to be implemented"}

@router.post("/")
async def create_warehouse(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create new warehouse"""
    return {"message": "Create warehouse endpoint - to be implemented"}
