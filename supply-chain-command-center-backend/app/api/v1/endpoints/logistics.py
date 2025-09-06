from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.core.database import get_database
from app.services.logistics_service import logistics_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/optimize-routes")
async def optimize_delivery_routes(
    request: Dict[str, Any] = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Optimize delivery routes using OR-Tools VRP solver"""
    try:
        warehouse_id = request.get("warehouse_id")
        delivery_requests = request.get("delivery_requests", [])
        vehicles = request.get("vehicles", [])
        optimization_type = request.get("optimization_type", "minimize_distance")
        
        if not warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="warehouse_id is required"
            )
        
        if not delivery_requests:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="delivery_requests cannot be empty"
            )
        
        if not vehicles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vehicles list cannot be empty"
            )
        
        result = await logistics_service.optimize_delivery_routes(
            db=db,
            warehouse_id=warehouse_id,
            delivery_requests=delivery_requests,
            vehicles=vehicles,
            optimization_type=optimization_type
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in route optimization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize routes"
        )

@router.get("/delivery-time-estimate")
async def get_delivery_time_estimate(
    from_location: str = Query(..., description="From location ID"),
    to_location: str = Query(..., description="To location ID"),
    traffic_factor: float = Query(1.0, ge=0.5, le=3.0, description="Traffic factor (1.0 = normal)"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Calculate estimated delivery time between two locations"""
    try:
        result = await logistics_service.calculate_delivery_time_estimate(
            db=db,
            from_location_id=from_location,
            to_location_id=to_location,
            traffic_factor=traffic_factor
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating delivery time: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate delivery time estimate"
        )

@router.post("/warehouse-allocation")
async def optimize_warehouse_allocation(
    orders: List[Dict[str, Any]] = Body(..., description="List of orders to allocate"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Optimize which warehouse should fulfill each order"""
    try:
        if not orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Orders list cannot be empty"
            )
        
        result = await logistics_service.optimize_warehouse_allocation(
            db=db,
            orders=orders
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in warehouse allocation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize warehouse allocation"
        )

@router.get("/demo/sample-request")
async def get_sample_optimization_request():
    """Get a sample request for route optimization (for testing/demo)"""
    return {
        "warehouse_id": "WH001",
        "delivery_requests": [
            {
                "id": "delivery_1",
                "customer_id": "CUST001",
                "customer_name": "Customer A",
                "latitude": 40.7589,
                "longitude": -73.9851,
                "address": "123 Customer St, NYC",
                "weight": 25.0,
                "priority": 1,
                "service_time": 30
            },
            {
                "id": "delivery_2",
                "customer_id": "CUST002",
                "customer_name": "Customer B",
                "latitude": 40.6892,
                "longitude": -74.0445,
                "address": "456 Business Ave, NYC",
                "weight": 15.0,
                "priority": 1,
                "service_time": 20
            },
            {
                "id": "delivery_3",
                "customer_id": "CUST003",
                "customer_name": "Customer C",
                "latitude": 40.7505,
                "longitude": -73.9934,
                "address": "789 Commerce Blvd, NYC",
                "weight": 30.0,
                "priority": 2,
                "service_time": 45
            }
        ],
        "vehicles": [
            {
                "id": "truck_1",
                "capacity": 100.0,
                "cost_per_km": 2.5,
                "max_distance": 200.0
            },
            {
                "id": "truck_2",
                "capacity": 150.0,
                "cost_per_km": 3.0,
                "max_distance": 250.0
            }
        ],
        "optimization_type": "minimize_distance"
    }

@router.get("/demo/sample-warehouse-allocation")
async def get_sample_warehouse_allocation():
    """Get a sample request for warehouse allocation optimization (for testing/demo)"""
    return {
        "orders": [
            {
                "id": "order_1",
                "customer_latitude": 40.7589,
                "customer_longitude": -73.9851,
                "items": [
                    {"sku": "LAPTOP001", "quantity": 2},
                    {"sku": "MOUSE001", "quantity": 5}
                ]
            },
            {
                "id": "order_2",
                "customer_latitude": 40.6892,
                "customer_longitude": -74.0445,
                "items": [
                    {"sku": "MONITOR001", "quantity": 1}
                ]
            }
        ]
    }
