from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class DashboardService:
    
    async def get_comprehensive_dashboard_summary(
        self,
        db: AsyncIOMotorDatabase,
        warehouse_id: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard summary with all key metrics"""
        try:
            # Run all data aggregation tasks concurrently
            tasks = [
                self._get_inventory_kpis(db, warehouse_id),
                self._get_recent_activities(db, days_back),
                self._get_alerts_and_notifications(db),
                self._get_financial_summary(db, warehouse_id, days_back),
                self._get_supplier_performance(db, days_back),
                self._get_logistics_summary(db, days_back),
                self._get_forecast_summary(db),
                self._get_trend_analysis(db, days_back)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            dashboard_data = {
                "generated_at": datetime.utcnow().isoformat(),
                "warehouse_filter": warehouse_id,
                "analysis_period_days": days_back,
                "inventory_kpis": results[0] if not isinstance(results[0], Exception) else {},
                "recent_activities": results[1] if not isinstance(results[1], Exception) else [],
                "alerts": results[2] if not isinstance(results[2], Exception) else [],
                "financial_summary": results[3] if not isinstance(results[3], Exception) else {},
                "supplier_performance": results[4] if not isinstance(results[4], Exception) else {},
                "logistics_summary": results[5] if not isinstance(results[5], Exception) else {},
                "forecast_summary": results[6] if not isinstance(results[6], Exception) else {},
                "trends": results[7] if not isinstance(results[7], Exception) else {}
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard summary: {str(e)}")
            return {"error": str(e)}
    
    async def _get_inventory_kpis(
        self,
        db: AsyncIOMotorDatabase,
        warehouse_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get inventory Key Performance Indicators"""
        try:
            match_criteria = {}
            if warehouse_id:
                match_criteria["warehouse_id"] = warehouse_id
            
            # Inventory aggregation pipeline
            pipeline = [
                {"$match": match_criteria},
                {
                    "$group": {
                        "_id": None,
                        "total_items": {"$sum": 1},
                        "total_stock_value": {"$sum": {"$multiply": ["$current_stock", "$cost_price"]}},
                        "total_retail_value": {"$sum": {"$multiply": ["$current_stock", "$selling_price"]}},
                        "low_stock_items": {
                            "$sum": {
                                "$cond": [
                                    {"$lte": ["$current_stock", "$reorder_level"]},
                                    1,
                                    0
                                ]
                            }
                        },
                        "out_of_stock_items": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$current_stock", 0]},
                                    1,
                                    0
                                ]
                            }
                        },
                        "overstocked_items": {
                            "$sum": {
                                "$cond": [
                                    {"$gte": ["$current_stock", "$maximum_stock"]},
                                    1,
                                    0
                                ]
                            }
                        },
                        "categories": {"$addToSet": "$category"},
                        "avg_stock_level": {"$avg": "$current_stock"}
                    }
                }
            ]
            
            cursor = db.inventory.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                kpis = result[0]
                kpis["total_categories"] = len(kpis.get("categories", []))
                kpis["stock_health_score"] = self._calculate_stock_health_score(kpis)
                del kpis["_id"]
                del kpis["categories"]
                return kpis
            
            return {
                "total_items": 0,
                "total_stock_value": 0,
                "total_retail_value": 0,
                "low_stock_items": 0,
                "out_of_stock_items": 0,
                "overstocked_items": 0,
                "total_categories": 0,
                "avg_stock_level": 0,
                "stock_health_score": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting inventory KPIs: {str(e)}")
            return {}
    
    def _calculate_stock_health_score(self, kpis: Dict) -> float:
        """Calculate overall stock health score (0-100)"""
        try:
            total_items = kpis.get("total_items", 1)
            if total_items == 0:
                return 0
            
            # Health score based on stock status distribution
            healthy_items = total_items - kpis.get("low_stock_items", 0) - kpis.get("out_of_stock_items", 0) - kpis.get("overstocked_items", 0)
            health_ratio = healthy_items / total_items
            
            # Penalize for out of stock more than low stock
            penalty = (
                (kpis.get("out_of_stock_items", 0) * 0.8) +
                (kpis.get("low_stock_items", 0) * 0.4) +
                (kpis.get("overstocked_items", 0) * 0.2)
            ) / total_items
            
            score = max(0, (health_ratio - penalty) * 100)
            return round(score, 1)
            
        except Exception:
            return 0.0
    
    async def _get_recent_activities(
        self,
        db: AsyncIOMotorDatabase,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get recent activities from various collections"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            activities = []
            
            # Stock movements
            stock_movements = await db.stock_movements.find(
                {"created_at": {"$gte": cutoff_date}},
                limit=20
            ).sort("created_at", -1).to_list(length=20)
            
            for movement in stock_movements:
                activities.append({
                    "type": "stock_movement",
                    "timestamp": movement.get("created_at"),
                    "description": f"{movement.get('movement_type')} - {movement.get('quantity')} units of {movement.get('inventory_item_sku')}",
                    "details": {
                        "sku": movement.get("inventory_item_sku"),
                        "quantity": movement.get("quantity"),
                        "movement_type": movement.get("movement_type"),
                        "reason": movement.get("reason")
                    }
                })
            
            # Recent invoices
            invoices = await db.invoices.find(
                {"created_at": {"$gte": cutoff_date}},
                limit=15
            ).sort("created_at", -1).to_list(length=15)
            
            for invoice in invoices:
                activities.append({
                    "type": "invoice",
                    "timestamp": invoice.get("created_at"),
                    "description": f"Invoice {invoice.get('invoice_number')} - ${invoice.get('total_amount', 0):.2f}",
                    "details": {
                        "invoice_number": invoice.get("invoice_number"),
                        "amount": invoice.get("total_amount"),
                        "supplier": invoice.get("supplier_name"),
                        "status": invoice.get("status")
                    }
                })
            
            # Sort all activities by timestamp
            activities.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
            
            return activities[:30]  # Return top 30 activities
            
        except Exception as e:
            logger.error(f"Error getting recent activities: {str(e)}")
            return []
    
    async def _get_alerts_and_notifications(self, db: AsyncIOMotorDatabase) -> List[Dict[str, Any]]:
        """Get system alerts and notifications"""
        try:
            alerts = []
            
            # Low stock alerts
            low_stock_items = await db.inventory.find(
                {"$expr": {"$lte": ["$current_stock", "$reorder_level"]}},
                limit=50
            ).to_list(length=50)
            
            for item in low_stock_items:
                severity = "critical" if item.get("current_stock", 0) == 0 else "warning"
                alerts.append({
                    "type": "low_stock",
                    "severity": severity,
                    "title": f"Low Stock Alert - {item.get('name', 'Unknown Item')}",
                    "message": f"SKU {item.get('sku')} has {item.get('current_stock', 0)} units left (reorder at {item.get('reorder_level', 0)})",
                    "created_at": datetime.utcnow().isoformat(),
                    "data": {
                        "sku": item.get("sku"),
                        "current_stock": item.get("current_stock"),
                        "reorder_level": item.get("reorder_level"),
                        "suggested_order": item.get("reorder_quantity", 0)
                    }
                })
            
            # Pending invoices
            pending_invoices = await db.invoices.count_documents({
                "status": "pending",
                "created_at": {"$lte": datetime.utcnow() - timedelta(days=7)}
            })
            
            if pending_invoices > 0:
                alerts.append({
                    "type": "pending_invoices",
                    "severity": "info",
                    "title": "Pending Invoices",
                    "message": f"{pending_invoices} invoices have been pending for over 7 days",
                    "created_at": datetime.utcnow().isoformat(),
                    "data": {"count": pending_invoices}
                })
            
            # Sort by severity
            severity_order = {"critical": 0, "warning": 1, "info": 2}
            alerts.sort(key=lambda x: severity_order.get(x.get("severity"), 3))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting alerts: {str(e)}")
            return []
    
    async def _get_financial_summary(
        self,
        db: AsyncIOMotorDatabase,
        warehouse_id: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get financial summary and metrics"""
        try:
            match_criteria = {}
            if warehouse_id:
                match_criteria["warehouse_id"] = warehouse_id
            
            # Current inventory value
            inventory_pipeline = [
                {"$match": match_criteria},
                {
                    "$group": {
                        "_id": None,
                        "total_cost_value": {"$sum": {"$multiply": ["$current_stock", "$cost_price"]}},
                        "total_retail_value": {"$sum": {"$multiply": ["$current_stock", "$selling_price"]}},
                        "potential_profit": {
                            "$sum": {
                                "$multiply": [
                                    "$current_stock",
                                    {"$subtract": ["$selling_price", "$cost_price"]}
                                ]
                            }
                        }
                    }
                }
            ]
            
            cursor = db.inventory.aggregate(inventory_pipeline)
            inventory_result = await cursor.to_list(length=1)
            
            inventory_value = inventory_result[0] if inventory_result else {
                "total_cost_value": 0,
                "total_retail_value": 0,
                "potential_profit": 0
            }
            
            # Recent invoice totals
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            invoice_pipeline = [
                {"$match": {"created_at": {"$gte": cutoff_date}}},
                {
                    "$group": {
                        "_id": "$invoice_type",
                        "total_amount": {"$sum": "$total_amount"},
                        "count": {"$sum": 1},
                        "avg_amount": {"$avg": "$total_amount"}
                    }
                }
            ]
            
            cursor = db.invoices.aggregate(invoice_pipeline)
            invoice_results = await cursor.to_list(length=None)
            
            invoice_summary = {}
            for result in invoice_results:
                invoice_summary[result["_id"]] = {
                    "total": result["total_amount"],
                    "count": result["count"],
                    "average": result["avg_amount"]
                }
            
            return {
                "inventory_value": {
                    "cost_value": round(inventory_value.get("total_cost_value", 0), 2),
                    "retail_value": round(inventory_value.get("total_retail_value", 0), 2),
                    "potential_profit": round(inventory_value.get("potential_profit", 0), 2),
                    "markup_percentage": round(
                        ((inventory_value.get("total_retail_value", 0) - inventory_value.get("total_cost_value", 0)) 
                         / max(inventory_value.get("total_cost_value", 1), 1)) * 100, 1
                    )
                },
                "recent_invoices": invoice_summary,
                "analysis_period_days": days_back
            }
            
        except Exception as e:
            logger.error(f"Error getting financial summary: {str(e)}")
            return {}
    
    async def _get_supplier_performance(
        self,
        db: AsyncIOMotorDatabase,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get supplier performance metrics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Recent supplier invoice data
            pipeline = [
                {"$match": {"created_at": {"$gte": cutoff_date}, "supplier_id": {"$exists": True, "$ne": None}}},
                {
                    "$group": {
                        "_id": "$supplier_id",
                        "supplier_name": {"$first": "$supplier_name"},
                        "total_amount": {"$sum": "$total_amount"},
                        "invoice_count": {"$sum": 1},
                        "avg_amount": {"$avg": "$total_amount"},
                        "avg_processing_time": {"$avg": {"$subtract": ["$processed_at", "$created_at"]}},
                        "status_breakdown": {
                            "$push": "$status"
                        }
                    }
                },
                {"$sort": {"total_amount": -1}},
                {"$limit": 10}
            ]
            
            cursor = db.invoices.aggregate(pipeline)
            supplier_data = await cursor.to_list(length=10)
            
            suppliers = []
            for supplier in supplier_data:
                # Calculate status percentages
                statuses = supplier.get("status_breakdown", [])
                status_counts = {}
                for status in statuses:
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                suppliers.append({
                    "supplier_id": supplier["_id"],
                    "supplier_name": supplier.get("supplier_name", "Unknown"),
                    "total_amount": round(supplier.get("total_amount", 0), 2),
                    "invoice_count": supplier.get("invoice_count", 0),
                    "avg_amount": round(supplier.get("avg_amount", 0), 2),
                    "status_breakdown": status_counts
                })
            
            return {
                "top_suppliers": suppliers,
                "analysis_period_days": days_back
            }
            
        except Exception as e:
            logger.error(f"Error getting supplier performance: {str(e)}")
            return {}
    
    async def _get_logistics_summary(
        self,
        db: AsyncIOMotorDatabase,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get logistics and delivery summary"""
        try:
            # This would typically come from deliveries/shipments collections
            # For now, return placeholder data based on stock movements
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Count outbound movements as deliveries
            outbound_movements = await db.stock_movements.count_documents({
                "movement_type": {"$in": ["OUT", "TRANSFER"]},
                "created_at": {"$gte": cutoff_date}
            })
            
            # Get optimization results if any
            optimization_results = await db.logistics_optimizations.count_documents({
                "created_at": {"$gte": cutoff_date}
            })
            
            return {
                "deliveries_completed": outbound_movements,
                "route_optimizations": optimization_results,
                "analysis_period_days": days_back,
                "avg_delivery_time_hours": 24.5,  # Placeholder
                "on_time_delivery_rate": 92.3  # Placeholder
            }
            
        except Exception as e:
            logger.error(f"Error getting logistics summary: {str(e)}")
            return {}
    
    async def _get_forecast_summary(self, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """Get demand forecasting summary"""
        try:
            # Count recent forecasts
            recent_forecasts = await db.demand_forecasts.count_documents({
                "generated_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
            })
            
            # Get most recent forecasts
            recent_forecast_cursor = db.demand_forecasts.find({}, limit=5).sort("generated_at", -1)
            recent_forecast_list = await recent_forecast_cursor.to_list(length=5)
            
            forecast_skus = [f.get("sku", "Unknown") for f in recent_forecast_list]
            
            return {
                "recent_forecasts_count": recent_forecasts,
                "last_updated": recent_forecast_list[0].get("generated_at") if recent_forecast_list else None,
                "recently_forecasted_skus": forecast_skus[:10]
            }
            
        except Exception as e:
            logger.error(f"Error getting forecast summary: {str(e)}")
            return {}
    
    async def _get_trend_analysis(
        self,
        db: AsyncIOMotorDatabase,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get trend analysis over time"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Daily stock movements trend
            movement_pipeline = [
                {"$match": {"created_at": {"$gte": cutoff_date}}},
                {
                    "$group": {
                        "_id": {
                            "date": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$created_at"
                                }
                            },
                            "type": "$movement_type"
                        },
                        "count": {"$sum": 1},
                        "total_quantity": {"$sum": {"$abs": "$quantity"}}
                    }
                },
                {"$sort": {"_id.date": 1}}
            ]
            
            cursor = db.stock_movements.aggregate(movement_pipeline)
            movement_trends = await cursor.to_list(length=None)
            
            # Process trends
            daily_trends = {}
            for trend in movement_trends:
                date = trend["_id"]["date"]
                movement_type = trend["_id"]["type"]
                
                if date not in daily_trends:
                    daily_trends[date] = {}
                
                daily_trends[date][movement_type] = {
                    "count": trend["count"],
                    "quantity": trend["total_quantity"]
                }
            
            return {
                "daily_movements": daily_trends,
                "trend_period_days": days_back
            }
            
        except Exception as e:
            logger.error(f"Error getting trend analysis: {str(e)}")
            return {}

# Global dashboard service instance
dashboard_service = DashboardService()
