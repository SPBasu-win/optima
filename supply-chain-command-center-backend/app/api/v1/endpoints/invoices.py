from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database

router = APIRouter()

@router.get("/")
async def get_invoices(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all invoices"""
    return {"message": "Invoice endpoints - to be implemented"}

@router.post("/upload")
async def upload_invoice(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Upload and process invoice with OCR"""
    return {"message": "Invoice upload endpoint - to be implemented"}
