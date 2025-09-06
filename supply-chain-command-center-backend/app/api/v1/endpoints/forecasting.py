from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import pandas as pd

from app.api.deps import get_database
from app.services.ml_services_simple import gemma_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/demand/{sku}")
async def get_demand_forecast(
    sku: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to forecast"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get demand forecast using Gemma model for a specific product"""
    try:
        # Check if product exists
        product = await db.inventory.find_one({"sku": sku})
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with SKU {sku} not found"
            )
        
        # Get historical data (simulate with recent activity or stock changes)
        # In a real system, this would come from sales/demand history
        historical_data = []
        
        # For demo, create some synthetic historical data based on current stock
        current_stock = product.get('current_stock', 100)
        base_demand = max(5, current_stock // 10)  # Estimate daily demand
        
        # Generate 30 days of historical data
        import random
        from datetime import datetime, timedelta
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=30-i)).strftime('%Y-%m-%d')
            # Add some variation to historical demand
            demand = max(1, int(base_demand * (0.8 + random.random() * 0.4)))
            cost = product.get('unit_price', 25.0) * (0.9 + random.random() * 0.2)
            
            historical_data.append({
                'date': date,
                'demand': demand,
                'cost': round(cost, 2)
            })
        
        # Use Gemma service to generate forecast
        forecast_result = await gemma_service.generate_demand_forecast(
            sku=sku,
            historical_data=historical_data,
            forecast_days=days
        )
        
        # Enhance with additional metadata
        enhanced_result = {
            **forecast_result,
            "sku": sku,
            "product_name": product.get('name', 'Unknown'),
            "current_stock": current_stock,
            "forecast_days": days,
            "generated_at": pd.Timestamp.now().isoformat(),
            "note": "Generated using Gemma AI model with historical pattern analysis"
        }
        
        return enhanced_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Gemma demand forecast endpoint for {sku}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate demand forecast with Gemma model"
        )


@router.get("/cost/{sku}")
async def get_cost_forecast(
    sku: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to forecast costs"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get cost forecast using Gemma model for a specific product"""
    try:
        # Check if product exists
        product = await db.inventory.find_one({"sku": sku})
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with SKU {sku} not found"
            )
        
        # Generate historical cost data
        historical_data = []
        current_price = product.get('unit_price', 25.0)
        
        # Generate 30 days of historical cost data
        import random
        from datetime import datetime, timedelta
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=30-i)).strftime('%Y-%m-%d')
            # Add some variation to historical costs (slight inflation trend)
            daily_variation = 1 + (random.random() - 0.5) * 0.1  # ±5% daily variation
            inflation_factor = 1 + (i * 0.001)  # 0.1% daily inflation
            cost = current_price * daily_variation * inflation_factor
            
            historical_data.append({
                'date': date,
                'demand': random.randint(5, 20),  # Random demand for context
                'cost': round(cost, 2)
            })
        
        # Use Gemma service to generate cost forecast
        forecast_result = await gemma_service.generate_cost_forecast(
            sku=sku,
            historical_data=historical_data,
            forecast_days=days
        )
        
        # Enhance with additional metadata
        enhanced_result = {
            **forecast_result,
            "sku": sku,
            "product_name": product.get('name', 'Unknown'),
            "current_price": current_price,
            "forecast_days": days,
            "generated_at": pd.Timestamp.now().isoformat(),
            "note": "Cost forecast generated using Gemma AI model"
        }
        
        return enhanced_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Gemma cost forecast endpoint for {sku}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cost forecast with Gemma model"
        )

@router.post("/generate")
async def generate_forecasts(
    skus: Optional[List[str]] = None,
    days: int = Query(30, ge=1, le=365, description="Number of days to forecast"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate forecasts for multiple products (batch processing)"""
    try:
        results = await forecasting_service.batch_generate_forecasts(
            db=db,
            skus=skus,
            days=days
        )
        return results
        
    except Exception as e:
        logger.error(f"Error in batch forecast generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate batch forecasts"
        )

@router.get("/accuracy/{sku}")
async def get_forecast_accuracy(
    sku: str,
    days_back: int = Query(30, ge=7, le=90, description="Days back to check accuracy"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get forecast accuracy for a product by comparing past forecasts with actual demand"""
    try:
        accuracy = await forecasting_service.get_forecast_accuracy(
            db=db,
            sku=sku,
            days_back=days_back
        )
        
        if "error" in accuracy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=accuracy["error"]
            )
        
        return accuracy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting forecast accuracy for {sku}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate forecast accuracy"
        )

@router.get("/stored/{sku}")
async def get_stored_forecast(
    sku: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get the most recent stored forecast for a product"""
    try:
        forecast = await forecasting_service.get_stored_forecast(db, sku)
        
        if not forecast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No stored forecast found for SKU {sku}"
            )
        
        return {
            "cached": True,
            **forecast
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stored forecast for {sku}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve stored forecast"
        )

@router.get("/insights/{sku}")
async def get_forecast_insights(
    sku: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get forecast insights and recommendations for a product"""
    try:
        # Get or generate forecast
        forecast = await forecasting_service.generate_demand_forecast(
            db=db,
            sku=sku,
            days=days,
            include_confidence=False
        )
        
        if "error" in forecast:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=forecast["error"]
            )
        
        # Return only insights and recommendations
        return {
            "sku": sku,
            "forecast_period_days": days,
            "insights": forecast.get("insights", {}),
            "summary": forecast.get("forecast", {}).get("summary", {}),
            "generated_at": forecast.get("generated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting forecast insights for {sku}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate forecast insights"
        )
