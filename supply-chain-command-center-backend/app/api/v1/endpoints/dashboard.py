from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.core.database import get_database
from app.services.dashboard_service import dashboard_service
from app.services.inventory_service import inventory_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/summary")
async def get_comprehensive_dashboard_summary(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse ID"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get comprehensive dashboard summary with all key metrics"""
    try:
        summary = await dashboard_service.get_comprehensive_dashboard_summary(
            db=db,
            warehouse_id=warehouse_id,
            days_back=days_back
        )
        
        if "error" in summary:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=summary["error"]
            )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dashboard summary"
        )

@router.get("/alerts")
async def get_system_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: critical, warning, info"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of alerts to return"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get system alerts and notifications"""
    try:
        # Get alerts from dashboard service
        dashboard_data = await dashboard_service.get_comprehensive_dashboard_summary(db, days_back=7)
        alerts = dashboard_data.get("alerts", [])
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.get("severity") == severity.lower()]
        
        # Limit results
        alerts = alerts[:limit]
        
        return {
            "alerts": alerts,
            "total_count": len(alerts),
            "severity_filter": severity,
            "generated_at": dashboard_data.get("generated_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting system alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system alerts"
        )

@router.get("/kpis")
async def get_key_performance_indicators(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse ID"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get key performance indicators for the supply chain"""
    try:
        # Get inventory KPIs
        inventory_summary = await inventory_service.get_inventory_summary(db, warehouse_id)
        
        # Get dashboard summary for additional KPIs
        dashboard_data = await dashboard_service.get_comprehensive_dashboard_summary(
            db, warehouse_id, days_back=30
        )
        
        kpis = {
            "inventory": inventory_summary,
            "financial": dashboard_data.get("financial_summary", {}),
            "logistics": dashboard_data.get("logistics_summary", {}),
            "supplier_performance": dashboard_data.get("supplier_performance", {}),
            "forecasting": dashboard_data.get("forecast_summary", {}),
            "generated_at": dashboard_data.get("generated_at")
        }
        
        return kpis
        
    except Exception as e:
        logger.error(f"Error getting KPIs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KPIs"
        )

@router.get("/activities")
async def get_recent_activities(
    days_back: int = Query(30, ge=1, le=90, description="Number of days to look back"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type: stock_movement, invoice, etc."),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of activities to return"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get recent activities across the supply chain"""
    try:
        dashboard_data = await dashboard_service.get_comprehensive_dashboard_summary(
            db, days_back=days_back
        )
        
        activities = dashboard_data.get("recent_activities", [])
        
        # Filter by activity type if specified
        if activity_type:
            activities = [activity for activity in activities if activity.get("type") == activity_type]
        
        # Limit results
        activities = activities[:limit]
        
        return {
            "activities": activities,
            "total_count": len(activities),
            "days_analyzed": days_back,
            "activity_type_filter": activity_type,
            "generated_at": dashboard_data.get("generated_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting recent activities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent activities"
        )

@router.get("/trends")
async def get_supply_chain_trends(
    days_back: int = Query(30, ge=7, le=90, description="Number of days for trend analysis"),
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse ID"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get supply chain trends and analytics"""
    try:
        dashboard_data = await dashboard_service.get_comprehensive_dashboard_summary(
            db, warehouse_id=warehouse_id, days_back=days_back
        )
        
        trends = {
            "movement_trends": dashboard_data.get("trends", {}),
            "inventory_trends": {
                "stock_health_score": dashboard_data.get("inventory_kpis", {}).get("stock_health_score", 0),
                "low_stock_trend": dashboard_data.get("inventory_kpis", {}).get("low_stock_items", 0),
                "total_value_trend": dashboard_data.get("inventory_kpis", {}).get("total_stock_value", 0)
            },
            "financial_trends": dashboard_data.get("financial_summary", {}),
            "supplier_trends": dashboard_data.get("supplier_performance", {}),
            "analysis_period": {
                "days_back": days_back,
                "warehouse_filter": warehouse_id,
                "generated_at": dashboard_data.get("generated_at")
            }
        }
        
        return trends
        
    except Exception as e:
        logger.error(f"Error getting supply chain trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supply chain trends"
        )

@router.get("/health-check")
async def get_system_health(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get overall system health metrics"""
    try:
        # Get basic health indicators
        dashboard_data = await dashboard_service.get_comprehensive_dashboard_summary(db, days_back=7)
        
        alerts = dashboard_data.get("alerts", [])
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
        warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
        
        inventory_kpis = dashboard_data.get("inventory_kpis", {})
        stock_health_score = inventory_kpis.get("stock_health_score", 0)
        
        # Calculate overall health score
        health_factors = {
            "stock_health": stock_health_score,
            "critical_issues": max(0, 100 - (len(critical_alerts) * 20)),  # Penalize critical alerts
            "warning_issues": max(0, 100 - (len(warning_alerts) * 10)),   # Penalize warnings less
            "data_freshness": 95  # Placeholder - could check data recency
        }
        
        overall_health = sum(health_factors.values()) / len(health_factors)
        
        health_status = "excellent" if overall_health >= 90 else \
                       "good" if overall_health >= 75 else \
                       "fair" if overall_health >= 60 else "poor"
        
        return {
            "overall_health_score": round(overall_health, 1),
            "health_status": health_status,
            "health_factors": health_factors,
            "alert_summary": {
                "critical": len(critical_alerts),
                "warning": len(warning_alerts),
                "info": len([a for a in alerts if a.get("severity") == "info"])
            },
            "inventory_health": {
                "stock_health_score": stock_health_score,
                "total_items": inventory_kpis.get("total_items", 0),
                "out_of_stock": inventory_kpis.get("out_of_stock_items", 0),
                "low_stock": inventory_kpis.get("low_stock_items", 0)
            },
            "generated_at": dashboard_data.get("generated_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health metrics"
        )

@router.get("/quick-stats")
async def get_quick_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get quick stats for dashboard widgets"""
    try:
        # Get basic stats quickly
        inventory_summary = await inventory_service.get_inventory_summary(db)
        dashboard_data = await dashboard_service.get_comprehensive_dashboard_summary(db, days_back=7)
        
        quick_stats = {
            "inventory": {
                "total_items": inventory_summary.get("total_items", 0),
                "total_value": inventory_summary.get("total_stock_value", 0),
                "low_stock_items": inventory_summary.get("low_stock_items", 0),
                "out_of_stock_items": inventory_summary.get("out_of_stock_items", 0)
            },
            "recent_activity": {
                "activities_count": len(dashboard_data.get("recent_activities", [])),
                "alerts_count": len(dashboard_data.get("alerts", [])),
                "critical_alerts": len([a for a in dashboard_data.get("alerts", []) if a.get("severity") == "critical"])
            },
            "forecasting": dashboard_data.get("forecast_summary", {}),
            "logistics": {
                "recent_deliveries": dashboard_data.get("logistics_summary", {}).get("deliveries_completed", 0),
                "route_optimizations": dashboard_data.get("logistics_summary", {}).get("route_optimizations", 0)
            },
            "generated_at": dashboard_data.get("generated_at")
        }
        
        return quick_stats
        
    except Exception as e:
        logger.error(f"Error getting quick stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quick stats"
        )
