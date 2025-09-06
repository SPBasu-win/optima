"""
Simplified Development Version of Supply Chain Command Center
This version works without MongoDB/Redis for easy local development
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
from pathlib import Path

# Simple in-memory data storage for development
inventory_data = {}
suppliers_data = {}
invoices_data = {}

# Data models
class InventoryItem(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: str
    current_stock: int
    minimum_stock: int
    cost_price: float
    selling_price: float
    warehouse_id: str = "WH001"
    supplier_id: str = "SUP001"
    created_at: datetime = None
    updated_at: datetime = None

class InventoryItemCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: str
    current_stock: int
    minimum_stock: int
    cost_price: float
    selling_price: float

class DashboardSummary(BaseModel):
    total_items: int
    low_stock_items: int
    total_value: float
    categories: int

app = FastAPI(
    title="Supply Chain Command Center API (Development)",
    description="Simplified development version of the supply chain management platform",
    version="1.0.0-dev",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load sample data
def load_sample_data():
    """Load some sample inventory data"""
    sample_items = [
        {
            "sku": "LAPTOP001",
            "name": "Dell Inspiron 15",
            "description": "15-inch laptop with Intel Core i5",
            "category": "Electronics",
            "current_stock": 25,
            "minimum_stock": 5,
            "cost_price": 450.00,
            "selling_price": 650.00,
            "warehouse_id": "WH001",
            "supplier_id": "SUP001",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "sku": "MOUSE001",
            "name": "Wireless Mouse",
            "description": "Ergonomic wireless mouse",
            "category": "Electronics",
            "current_stock": 2,  # Low stock
            "minimum_stock": 10,
            "cost_price": 15.00,
            "selling_price": 25.00,
            "warehouse_id": "WH001",
            "supplier_id": "SUP002",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "sku": "DESK001",
            "name": "Office Desk",
            "description": "Adjustable height office desk",
            "category": "Furniture",
            "current_stock": 15,
            "minimum_stock": 3,
            "cost_price": 200.00,
            "selling_price": 350.00,
            "warehouse_id": "WH002",
            "supplier_id": "SUP003",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]
    
    for item in sample_items:
        inventory_data[item["sku"]] = item

# Load sample data on startup
load_sample_data()

# Root endpoints
@app.get("/")
async def root():
    return {
        "message": "Supply Chain Command Center API (Development Version)",
        "version": "1.0.0-dev",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Inventory endpoints
@app.get("/api/v1/inventory/", response_model=List[Dict[str, Any]])
async def get_inventory(
    category: Optional[str] = None,
    low_stock_only: bool = False,
    limit: int = 100
):
    """Get inventory items with optional filtering"""
    items = list(inventory_data.values())
    
    # Apply filters
    if category:
        items = [item for item in items if item["category"].lower() == category.lower()]
    
    if low_stock_only:
        items = [item for item in items if item["current_stock"] <= item["minimum_stock"]]
    
    return items[:limit]

@app.get("/api/v1/inventory/{sku}")
async def get_inventory_item(sku: str):
    """Get specific inventory item by SKU"""
    if sku not in inventory_data:
        raise HTTPException(status_code=404, detail="Item not found")
    return inventory_data[sku]

@app.post("/api/v1/inventory/", response_model=Dict[str, Any])
async def create_inventory_item(item: InventoryItemCreate):
    """Create new inventory item"""
    if item.sku in inventory_data:
        raise HTTPException(status_code=400, detail="Item with this SKU already exists")
    
    # Create new item
    new_item = {
        **item.dict(),
        "warehouse_id": "WH001",
        "supplier_id": "SUP001", 
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    inventory_data[item.sku] = new_item
    return new_item

@app.put("/api/v1/inventory/{sku}")
async def update_inventory_item(sku: str, updates: Dict[str, Any]):
    """Update inventory item"""
    if sku not in inventory_data:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update item
    inventory_data[sku].update(updates)
    inventory_data[sku]["updated_at"] = datetime.now()
    
    return inventory_data[sku]

@app.delete("/api/v1/inventory/{sku}")
async def delete_inventory_item(sku: str):
    """Delete inventory item"""
    if sku not in inventory_data:
        raise HTTPException(status_code=404, detail="Item not found")
    
    deleted_item = inventory_data.pop(sku)
    return {"message": "Item deleted", "deleted_item": deleted_item}

# Low stock alerts
@app.get("/api/v1/inventory/low-stock/items")
async def get_low_stock_items():
    """Get items with low stock"""
    low_stock_items = [
        item for item in inventory_data.values() 
        if item["current_stock"] <= item["minimum_stock"]
    ]
    return {
        "count": len(low_stock_items),
        "items": low_stock_items
    }

# Dashboard endpoint
@app.get("/api/v1/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """Get dashboard summary data"""
    items = list(inventory_data.values())
    
    total_items = len(items)
    low_stock_items = len([item for item in items if item["current_stock"] <= item["minimum_stock"]])
    total_value = sum(item["current_stock"] * item["cost_price"] for item in items)
    categories = len(set(item["category"] for item in items))
    
    return DashboardSummary(
        total_items=total_items,
        low_stock_items=low_stock_items,
        total_value=round(total_value, 2),
        categories=categories
    )

@app.get("/api/v1/dashboard/kpis")
async def get_dashboard_kpis():
    """Get key performance indicators"""
    items = list(inventory_data.values())
    
    return {
        "total_inventory_value": sum(item["current_stock"] * item["cost_price"] for item in items),
        "total_items": len(items),
        "low_stock_alerts": len([item for item in items if item["current_stock"] <= item["minimum_stock"]]),
        "categories_count": len(set(item["category"] for item in items)),
        "avg_stock_level": sum(item["current_stock"] for item in items) / len(items) if items else 0
    }

# Simple forecasting endpoint (mock data for now)
@app.get("/api/v1/forecasting/demand/{sku}")
async def get_demand_forecast(sku: str, days: int = 30):
    """Get demand forecast for a product (mock data)"""
    if sku not in inventory_data:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Generate mock forecast data
    import random
    base_demand = random.randint(1, 10)
    forecast_data = []
    
    for day in range(1, days + 1):
        demand = max(0, base_demand + random.randint(-3, 5))
        forecast_data.append({
            "day": day,
            "predicted_demand": demand,
            "date": (datetime.now().date().replace(day=day)).isoformat() if day <= 28 else None
        })
    
    return {
        "sku": sku,
        "forecast_days": days,
        "forecast": forecast_data,
        "total_predicted_demand": sum(item["predicted_demand"] for item in forecast_data),
        "note": "This is mock data for development. Install Prophet for real forecasting."
    }

# Suppliers endpoint
@app.get("/api/v1/suppliers/")
async def get_suppliers():
    """Get suppliers list"""
    return [
        {"id": "SUP001", "name": "Tech Supplier Inc", "category": "Electronics", "performance_score": 95, "delivery_time": 3},
        {"id": "SUP002", "name": "Office Equipment Co", "category": "Electronics", "performance_score": 88, "delivery_time": 5},
        {"id": "SUP003", "name": "Furniture Plus", "category": "Furniture", "performance_score": 92, "delivery_time": 7}
    ]

# Analytics endpoints
@app.get("/api/v1/analytics/supply-chain-health")
async def get_supply_chain_health():
    """Get supply chain health metrics"""
    return {
        "overall_health_score": 85,
        "inventory_turnover": 6.2,
        "supplier_reliability": 91,
        "demand_accuracy": 78,
        "logistics_efficiency": 82,
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/v1/analytics/trends")
async def get_analytics_trends():
    """Get supply chain trends and insights"""
    return {
        "inventory_trends": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "data": [12000, 13500, 11800, 14200, 15600, 14800]
        },
        "demand_patterns": {
            "high_demand_items": ["LAPTOP001", "MOUSE001"],
            "declining_items": ["DESK001"],
            "seasonal_items": []
        },
        "cost_analysis": {
            "total_inventory_cost": 145280.50,
            "monthly_savings": 5420.30,
            "efficiency_score": 78
        }
    }

# Data Management endpoints
@app.get("/api/v1/data-management/overview")
async def get_data_overview():
    """Get data management overview"""
    return {
        "total_records": 12847,
        "clean_records": 12203,
        "error_records": 644,
        "last_updated": "2024-01-15T14:30:00",
        "data_quality_score": 95,
        "recent_activities": [
            {"activity": "Data Import", "timestamp": "2024-01-15T10:00:00", "status": "completed", "records_processed": 1250},
            {"activity": "Data Cleaning", "timestamp": "2024-01-15T12:30:00", "status": "completed", "errors_fixed": 45},
            {"activity": "Error Review", "timestamp": "2024-01-15T14:15:00", "status": "in-progress", "errors_remaining": 12}
        ]
    }

@app.post("/api/v1/data-management/import")
async def import_data(file_type: str = "csv", source: str = "manual"):
    """Import data from various sources"""
    # Simulate data import process
    import random
    import time
    
    # Simulate processing time
    processing_time = random.uniform(1, 3)
    records_imported = random.randint(100, 1000)
    
    return {
        "status": "success",
        "message": f"Successfully imported {records_imported} records from {source}",
        "records_imported": records_imported,
        "processing_time": round(processing_time, 2),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/data-management/clean")
async def clean_data():
    """Clean and validate data"""
    return {
        "status": "completed",
        "records_cleaned": 156,
        "errors_fixed": 23,
        "duplicates_removed": 8,
        "data_quality_improvement": 3.2,
        "timestamp": datetime.now().isoformat()
    }

# Enhanced inventory endpoints
@app.post("/api/v1/inventory/bulk-update")
async def bulk_update_inventory(updates: List[Dict[str, Any]]):
    """Bulk update inventory items"""
    updated_items = []
    for update in updates:
        sku = update.get("sku")
        if sku in inventory_data:
            inventory_data[sku].update(update)
            inventory_data[sku]["updated_at"] = datetime.now()
            updated_items.append(inventory_data[sku])
    
    return {
        "status": "success",
        "updated_items": len(updated_items),
        "items": updated_items
    }

# Stock management endpoints
@app.post("/api/v1/inventory/{sku}/update-stock")
async def update_stock(sku: str, new_stock: int, reason: str = "Manual adjustment"):
    """Update stock level for specific item"""
    if sku not in inventory_data:
        raise HTTPException(status_code=404, detail="Item not found")
    
    old_stock = inventory_data[sku]["current_stock"]
    inventory_data[sku]["current_stock"] = new_stock
    inventory_data[sku]["updated_at"] = datetime.now()
    
    # Create stock movement record (you could store this in a database)
    movement_record = {
        "sku": sku,
        "previous_stock": old_stock,
        "new_stock": new_stock,
        "change": new_stock - old_stock,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "status": "success",
        "message": f"Stock updated from {old_stock} to {new_stock}",
        "item": inventory_data[sku],
        "movement": movement_record
    }

@app.get("/api/v1/inventory/{sku}/stock-history")
async def get_stock_history(sku: str):
    """Get stock movement history for an item"""
    if sku not in inventory_data:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Mock stock history data
    import random
    from datetime import timedelta
    
    history = []
    current_date = datetime.now()
    current_stock = inventory_data[sku]["current_stock"]
    
    # Generate mock history for the last 7 days
    for i in range(7):
        date = current_date - timedelta(days=i)
        change = random.randint(-10, 15)
        previous_stock = current_stock - change
        
        history.append({
            "date": date.isoformat(),
            "previous_stock": previous_stock,
            "new_stock": current_stock,
            "change": change,
            "reason": random.choice(["Sale", "Restock", "Manual adjustment", "Return"])
        })
        current_stock = previous_stock
    
    return {
        "sku": sku,
        "current_stock": inventory_data[sku]["current_stock"],
        "history": history[::-1]  # Reverse to show oldest first
    }

# Notifications endpoint
@app.get("/api/v1/notifications")
async def get_notifications():
    """Get system notifications"""
    notifications = []
    
    # Check for low stock items
    for item in inventory_data.values():
        if item["current_stock"] <= item["minimum_stock"]:
            notifications.append({
                "id": f"low-stock-{item['sku']}",
                "type": "warning" if item["current_stock"] > 0 else "error",
                "title": f"Low Stock Alert: {item['name']}",
                "message": f"Only {item['current_stock']} units remaining (min: {item['minimum_stock']})",
                "timestamp": datetime.now().isoformat(),
                "action_url": f"/inventory/{item['sku']}"
            })
    
    return {
        "notifications": notifications,
        "unread_count": len(notifications)
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Supply Chain Command Center (Development Mode)")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🌐 API Base URL: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
