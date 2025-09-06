"""
CSV ML API Endpoints

This module provides API endpoints for:
1. CSV file upload and ML analysis
2. Demand forecasting with CSV data
3. Inventory optimization with CSV data
4. Data pattern analysis and insights
"""

import io
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import pandas as pd
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_database
from app.services.csv_ml_service import csv_ml_service

router = APIRouter()
logger = logging.getLogger(__name__)

# ===== REQUEST/RESPONSE MODELS =====

class CSVAnalysisResponse(BaseModel):
    """Response model for CSV analysis"""
    success: bool
    filename: str
    data_analysis: Dict[str, Any]
    data_patterns: Dict[str, Any]
    recommended_ml_tasks: List[str]
    columns: List[str]
    preview: List[Dict[str, Any]]

class ForecastRequest(BaseModel):
    """Request model for demand forecasting"""
    date_column: str = Field(..., description="Name of the date column")
    demand_column: str = Field(..., description="Name of the demand/sales column")
    product_column: Optional[str] = Field(None, description="Name of the product column (optional)")
    forecast_days: int = Field(30, ge=1, le=365, description="Number of days to forecast")

class ForecastResponse(BaseModel):
    """Response model for demand forecasting"""
    success: bool
    forecast_results: Dict[str, Any]
    data_points_used: int
    forecast_horizon_days: int
    generated_at: str

class OptimizationRequest(BaseModel):
    """Request model for inventory optimization"""
    product_column: str = Field(..., description="Name of the product column")
    stock_column: str = Field(..., description="Name of the stock/quantity column")
    sales_column: Optional[str] = Field(None, description="Name of the sales column (optional)")
    cost_column: Optional[str] = Field(None, description="Name of the cost/price column (optional)")

class OptimizationResponse(BaseModel):
    """Response model for inventory optimization"""
    success: bool
    inventory_analysis: Dict[str, Any]
    optimization_results: Dict[str, Any]
    abc_analysis: Dict[str, Any]
    stock_recommendations: Dict[str, Any]
    generated_at: str

# In-memory storage for CSV data (in production, use Redis or database)
csv_data_storage: Dict[str, pd.DataFrame] = {}

# ===== ENDPOINTS =====

@router.post("/analyze", response_model=CSVAnalysisResponse)
async def analyze_csv_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> CSVAnalysisResponse:
    """
    Upload and analyze CSV file for ML capabilities
    
    This endpoint:
    1. Validates and processes the CSV file
    2. Analyzes data structure and quality
    3. Detects patterns and trends
    4. Recommends suitable ML tasks
    5. Provides data preview
    """
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['csv']:
        raise HTTPException(
            status_code=400, 
            detail="Only CSV files are supported for ML analysis"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Initialize CSV ML service
        if not csv_ml_service._initialized:
            await csv_ml_service.initialize()
        
        # Process CSV file
        analysis_result = await csv_ml_service.process_csv_file(content, file.filename)
        
        if not analysis_result["success"]:
            raise HTTPException(status_code=400, detail=analysis_result["error"])
        
        # Store processed data for later use
        import uuid
        session_id = str(uuid.uuid4())
        
        # Convert cleaned data back to DataFrame and store
        df = pd.DataFrame(analysis_result["cleaned_data"])
        csv_data_storage[session_id] = df
        
        # Add session_id to response for subsequent requests
        analysis_result["session_id"] = session_id
        
        logger.info(f"CSV file analyzed successfully: {file.filename}, session: {session_id}")
        
        return CSVAnalysisResponse(
            success=True,
            filename=analysis_result["filename"],
            data_analysis=analysis_result["data_analysis"],
            data_patterns=analysis_result["data_patterns"],
            recommended_ml_tasks=analysis_result["data_analysis"]["recommended_ml_tasks"],
            columns=analysis_result["columns"],
            preview=analysis_result["preview"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing CSV file: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing CSV file: {str(e)}")


@router.post("/forecast/{session_id}", response_model=ForecastResponse)
async def forecast_demand_csv(
    session_id: str,
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ForecastResponse:
    """
    Generate demand forecast from CSV data
    
    This endpoint:
    1. Uses previously uploaded CSV data
    2. Applies Prophet or fallback forecasting models
    3. Generates predictions for specified time horizon
    4. Provides model performance metrics
    5. Returns structured forecast results
    """
    
    # Validate session
    if session_id not in csv_data_storage:
        raise HTTPException(status_code=404, detail="CSV session not found. Please upload a file first.")
    
    df = csv_data_storage[session_id]
    
    # Validate required columns
    if request.date_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Date column '{request.date_column}' not found in data")
    
    if request.demand_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Demand column '{request.demand_column}' not found in data")
    
    if request.product_column and request.product_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Product column '{request.product_column}' not found in data")
    
    try:
        # Initialize service
        if not csv_ml_service._initialized:
            await csv_ml_service.initialize()
        
        # Generate forecast
        forecast_result = await csv_ml_service.forecast_demand_from_csv(
            df=df,
            date_col=request.date_column,
            demand_col=request.demand_column,
            product_col=request.product_column,
            forecast_days=request.forecast_days
        )
        
        if not forecast_result["success"]:
            raise HTTPException(status_code=400, detail=forecast_result["error"])
        
        logger.info(f"Demand forecast generated for session: {session_id}")
        
        return ForecastResponse(
            success=True,
            forecast_results=forecast_result["forecast_results"],
            data_points_used=forecast_result["data_points_used"],
            forecast_horizon_days=forecast_result["forecast_horizon_days"],
            generated_at=forecast_result["generated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")


@router.post("/optimize/{session_id}", response_model=OptimizationResponse)
async def optimize_inventory_csv(
    session_id: str,
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> OptimizationResponse:
    """
    Optimize inventory based on CSV data
    
    This endpoint:
    1. Analyzes inventory levels and patterns
    2. Performs ABC analysis for product classification
    3. Generates optimization recommendations
    4. Identifies reorder points and excess stock
    5. Provides actionable stock management insights
    """
    
    # Validate session
    if session_id not in csv_data_storage:
        raise HTTPException(status_code=404, detail="CSV session not found. Please upload a file first.")
    
    df = csv_data_storage[session_id]
    
    # Validate required columns
    required_columns = [request.product_column, request.stock_column]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise HTTPException(
            status_code=400, 
            detail=f"Required columns not found: {missing_columns}"
        )
    
    # Validate optional columns
    if request.sales_column and request.sales_column not in df.columns:
        raise HTTPException(
            status_code=400, 
            detail=f"Sales column '{request.sales_column}' not found in data"
        )
    
    if request.cost_column and request.cost_column not in df.columns:
        raise HTTPException(
            status_code=400, 
            detail=f"Cost column '{request.cost_column}' not found in data"
        )
    
    try:
        # Initialize service
        if not csv_ml_service._initialized:
            await csv_ml_service.initialize()
        
        # Generate optimization
        optimization_result = await csv_ml_service.optimize_inventory_from_csv(
            df=df,
            product_col=request.product_column,
            stock_col=request.stock_column,
            sales_col=request.sales_column,
            cost_col=request.cost_column
        )
        
        if not optimization_result["success"]:
            raise HTTPException(status_code=400, detail=optimization_result["error"])
        
        logger.info(f"Inventory optimization completed for session: {session_id}")
        
        return OptimizationResponse(
            success=True,
            inventory_analysis=optimization_result["inventory_analysis"],
            optimization_results=optimization_result["optimization_results"],
            abc_analysis=optimization_result["abc_analysis"],
            stock_recommendations=optimization_result["stock_recommendations"],
            generated_at=optimization_result["generated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing inventory: {e}")
        raise HTTPException(status_code=500, detail=f"Error optimizing inventory: {str(e)}")


@router.get("/sessions")
async def list_csv_sessions():
    """List all active CSV ML sessions"""
    sessions = []
    
    for session_id, df in csv_data_storage.items():
        sessions.append({
            "session_id": session_id,
            "data_shape": df.shape,
            "columns": df.columns.tolist(),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        })
    
    return {"sessions": sessions, "total_sessions": len(sessions)}


@router.get("/session/{session_id}/info")
async def get_csv_session_info(session_id: str):
    """Get information about a specific CSV session"""
    if session_id not in csv_data_storage:
        raise HTTPException(status_code=404, detail="CSV session not found")
    
    df = csv_data_storage[session_id]
    
    # Basic statistics
    numeric_cols = df.select_dtypes(include=['number']).columns
    stats = {}
    
    for col in numeric_cols[:10]:  # Limit to first 10 numeric columns
        stats[col] = {
            "mean": round(df[col].mean(), 2),
            "median": round(df[col].median(), 2),
            "min": round(df[col].min(), 2),
            "max": round(df[col].max(), 2),
            "std": round(df[col].std(), 2)
        }
    
    return {
        "session_id": session_id,
        "data_shape": df.shape,
        "columns": df.columns.tolist(),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "numeric_stats": stats,
        "sample_data": df.head(5).to_dict('records'),
        "missing_data": {col: df[col].isnull().sum() for col in df.columns}
    }


@router.delete("/session/{session_id}")
async def delete_csv_session(session_id: str):
    """Delete a CSV ML session"""
    if session_id not in csv_data_storage:
        raise HTTPException(status_code=404, detail="CSV session not found")
    
    del csv_data_storage[session_id]
    
    return {"message": "CSV session deleted successfully"}


@router.post("/batch-forecast/{session_id}")
async def batch_forecast_products(
    session_id: str,
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    limit: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate forecasts for multiple products in batch
    
    This endpoint processes multiple products from the CSV data
    and generates individual forecasts for each product.
    """
    
    # Validate session
    if session_id not in csv_data_storage:
        raise HTTPException(status_code=404, detail="CSV session not found")
    
    df = csv_data_storage[session_id]
    
    # Validate columns
    if not request.product_column or request.product_column not in df.columns:
        raise HTTPException(status_code=400, detail="Product column is required for batch forecasting")
    
    if request.date_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Date column '{request.date_column}' not found")
    
    if request.demand_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Demand column '{request.demand_column}' not found")
    
    try:
        # Get unique products (limit to prevent overload)
        products = df[request.product_column].unique()[:limit]
        
        batch_results = {
            "total_products": len(products),
            "successful_forecasts": 0,
            "failed_forecasts": 0,
            "results": {}
        }
        
        # Initialize service
        if not csv_ml_service._initialized:
            await csv_ml_service.initialize()
        
        # Generate forecast for each product
        for product in products:
            try:
                product_df = df[df[request.product_column] == product]
                
                if len(product_df) < 10:  # Skip products with insufficient data
                    batch_results["failed_forecasts"] += 1
                    batch_results["results"][str(product)] = {
                        "error": "Insufficient data points (minimum 10 required)"
                    }
                    continue
                
                # Generate individual forecast
                forecast_result = await csv_ml_service.forecast_demand_from_csv(
                    df=product_df,
                    date_col=request.date_column,
                    demand_col=request.demand_column,
                    product_col=None,  # Single product, no grouping needed
                    forecast_days=request.forecast_days
                )
                
                if forecast_result["success"]:
                    batch_results["successful_forecasts"] += 1
                    batch_results["results"][str(product)] = forecast_result
                else:
                    batch_results["failed_forecasts"] += 1
                    batch_results["results"][str(product)] = {"error": forecast_result.get("error", "Unknown error")}
                
            except Exception as e:
                batch_results["failed_forecasts"] += 1
                batch_results["results"][str(product)] = {"error": str(e)}
        
        logger.info(f"Batch forecast completed: {batch_results['successful_forecasts']} successful, {batch_results['failed_forecasts']} failed")
        
        return batch_results
        
    except Exception as e:
        logger.error(f"Error in batch forecasting: {e}")
        raise HTTPException(status_code=500, detail=f"Error in batch forecasting: {str(e)}")


@router.post("/quick-insights/{session_id}")
async def get_quick_insights(
    session_id: str,
    background_tasks: BackgroundTasks
):
    """
    Get quick ML insights from CSV data
    
    This endpoint provides rapid analysis including:
    - Data quality assessment
    - Key patterns and trends
    - Recommended actions
    - Statistical summary
    """
    
    if session_id not in csv_data_storage:
        raise HTTPException(status_code=404, detail="CSV session not found")
    
    df = csv_data_storage[session_id]
    
    try:
        insights = {
            "data_overview": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
                "data_types": df.dtypes.value_counts().to_dict()
            },
            "data_quality": {
                "complete_rows": len(df.dropna()),
                "missing_data_percentage": round((df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2),
                "columns_with_missing_data": df.columns[df.isnull().any()].tolist()
            },
            "key_insights": [],
            "recommended_actions": []
        }
        
        # Generate key insights
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            insights["key_insights"].append(f"Dataset contains {len(numeric_cols)} numeric columns suitable for ML analysis")
            
            # High variance columns
            high_var_cols = []
            for col in numeric_cols:
                if df[col].std() > df[col].mean():
                    high_var_cols.append(col)
            
            if high_var_cols:
                insights["key_insights"].append(f"High variance detected in: {', '.join(high_var_cols[:3])}")
        
        # Date columns for time series
        date_cols = []
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    pd.to_datetime(df[col], errors='raise')
                    date_cols.append(col)
                except:
                    pass
        
        if date_cols:
            insights["key_insights"].append(f"Time series analysis possible with columns: {', '.join(date_cols)}")
            insights["recommended_actions"].append("Consider demand forecasting with time series data")
        
        # Inventory-related insights
        inventory_keywords = ['stock', 'quantity', 'inventory', 'units']
        inventory_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in inventory_keywords)]
        
        if inventory_cols:
            insights["key_insights"].append(f"Inventory data detected in columns: {', '.join(inventory_cols)}")
            insights["recommended_actions"].append("Run inventory optimization analysis")
        
        # Data quality recommendations
        if insights["data_quality"]["missing_data_percentage"] > 10:
            insights["recommended_actions"].append("Address missing data before ML analysis")
        
        if len(df) > 10000:
            insights["recommended_actions"].append("Large dataset detected - consider sampling for faster processing")
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating quick insights: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")


# Initialize CSV ML service on startup
@router.on_event("startup")
async def startup_event():
    """Initialize CSV ML service"""
    try:
        await csv_ml_service.initialize()
        logger.info("CSV ML service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize CSV ML service: {e}")
