from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime

from app.core.database import get_database
from app.models.inventory import (
    InventoryItem, InventoryItemCreate, InventoryItemUpdate, 
    StockMovement, InventoryFilter, StockStatus
)
from app.services.inventory_service import inventory_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[InventoryItem])
async def get_inventory_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    supplier_id: Optional[str] = Query(None, description="Filter by supplier"),
    status: Optional[StockStatus] = Query(None, description="Filter by status"),
    low_stock_only: bool = Query(False, description="Show only low stock items"),
    search: Optional[str] = Query(None, description="Search in name, SKU, description"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get inventory items with filtering and pagination"""
    try:
        filter_params = InventoryFilter(
            category=category,
            warehouse_id=warehouse_id,
            supplier_id=supplier_id,
            status=status,
            low_stock_only=low_stock_only,
            search=search,
            skip=skip,
            limit=limit
        )
        
        items = await inventory_service.get_inventory_items(db, filter_params)
        return items
    except Exception as e:
        logger.error(f"Error fetching inventory items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch inventory items"
        )

@router.get("/{sku}", response_model=InventoryItem)
async def get_inventory_item(
    sku: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get a specific inventory item by SKU"""
    try:
        item = await inventory_service.get_inventory_item_by_sku(db, sku)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item with SKU {sku} not found"
            )
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching inventory item {sku}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch inventory item"
        )

@router.post("/", response_model=InventoryItem, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item_data: InventoryItemCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new inventory item"""
    try:
        # Check if SKU already exists
        existing_item = await inventory_service.get_inventory_item_by_sku(db, item_data.sku)
        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Inventory item with SKU {item_data.sku} already exists"
            )
        
        new_item = await inventory_service.create_inventory_item(db, item_data)
        return new_item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating inventory item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create inventory item"
        )

@router.put("/{sku}", response_model=InventoryItem)
async def update_inventory_item(
    sku: str,
    update_data: InventoryItemUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update an existing inventory item"""
    try:
        updated_item = await inventory_service.update_inventory_item(db, sku, update_data)
        if not updated_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item with SKU {sku} not found"
            )
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating inventory item {sku}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update inventory item"
        )

@router.delete("/{sku}")
async def delete_inventory_item(
    sku: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete an inventory item"""
    try:
        success = await inventory_service.delete_inventory_item(db, sku)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item with SKU {sku} not found"
            )
        return {"message": f"Inventory item {sku} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting inventory item {sku}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete inventory item"
        )

@router.post("/{sku}/stock-movement", response_model=StockMovement)
async def record_stock_movement(
    sku: str,
    movement_type: str,
    quantity: int,
    reason: str,
    reference_number: Optional[str] = None,
    notes: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Record a stock movement (IN, OUT, ADJUSTMENT, TRANSFER)"""
    try:
        movement = await inventory_service.record_stock_movement(
            db=db,
            sku=sku,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            reference_number=reference_number,
            notes=notes
        )
        return movement
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error recording stock movement for {sku}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record stock movement"
        )

@router.get("/{sku}/stock-movements", response_model=List[StockMovement])
async def get_stock_movements(
    sku: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of movements to return"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get stock movement history for an item"""
    try:
        movements = await inventory_service.get_stock_movements(db, sku, limit)
        return movements
    except Exception as e:
        logger.error(f"Error fetching stock movements for {sku}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch stock movements"
        )

@router.get("/low-stock/items", response_model=List[InventoryItem])
async def get_low_stock_items(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get items that are at or below their reorder level"""
    try:
        items = await inventory_service.get_low_stock_items(db, warehouse_id)
        return items
    except Exception as e:
        logger.error(f"Error fetching low stock items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch low stock items"
        )

@router.post("/reorder/suggestions")
async def get_reorder_suggestions(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get automatic reorder suggestions based on current stock levels and historical data"""
    try:
        suggestions = await inventory_service.get_reorder_suggestions(db, warehouse_id)
        return suggestions
    except Exception as e:
        logger.error(f"Error generating reorder suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate reorder suggestions"
        )

@router.post("/deduplicate")
async def deduplicate_inventory(
    dry_run: bool = Query(True, description="If true, only return potential duplicates without removing them"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Identify and optionally remove duplicate inventory items"""
    try:
        result = await inventory_service.deduplicate_inventory(db, dry_run)
        return result
    except Exception as e:
        logger.error(f"Error deduplicating inventory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deduplicate inventory"
        )

@router.get("/analytics/summary")
async def get_inventory_summary(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get inventory analytics summary"""
    try:
        summary = await inventory_service.get_inventory_summary(db, warehouse_id)
        return summary
    except Exception as e:
        logger.error(f"Error generating inventory summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate inventory summary"
        )

@router.get("/categories/list")
async def get_categories(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get list of all inventory categories"""
    try:
        categories = await inventory_service.get_categories(db)
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories"
        )
