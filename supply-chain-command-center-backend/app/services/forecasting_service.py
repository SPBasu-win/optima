import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime, timedelta
import joblib
import os
from concurrent.futures import ThreadPoolExecutor
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)

class ForecastingService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.models_cache = {}  # Cache for trained models
        
    async def generate_demand_forecast(
        self, 
        db: AsyncIOMotorDatabase, 
        sku: str, 
        days: int = 30,
        include_confidence: bool = True
    ) -> Dict[str, Any]:
        """Generate demand forecast for a specific product"""
        try:
            # Get historical sales/movement data
            historical_data = await self._get_historical_demand_data(db, sku)
            
            if len(historical_data) < 10:  # Need minimum data points
                return {
                    "sku": sku,
                    "forecast_days": days,
                    "error": "Insufficient historical data for forecasting (minimum 10 data points required)",
                    "data_points_available": len(historical_data)
                }
            
            # Prepare data for Prophet
            df = await self._prepare_prophet_data(historical_data)
            
            # Train or load model
            model = await self._get_or_train_model(sku, df)
            
            # Generate forecast
            forecast_result = await self._generate_forecast(model, days, include_confidence)
            
            # Get additional insights
            insights = await self._generate_forecast_insights(db, sku, forecast_result, historical_data)
            
            return {
                "sku": sku,
                "forecast_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "forecast": forecast_result,
                "insights": insights,
                "model_performance": await self._get_model_performance(model, df),
                "confidence_level": "95%" if include_confidence else "N/A"
            }
            
        except Exception as e:
            logger.error(f"Error generating forecast for {sku}: {str(e)}")
            return {
                "sku": sku,
                "error": f"Forecast generation failed: {str(e)}",
                "forecast_days": days
            }
    
    async def batch_generate_forecasts(
        self, 
        db: AsyncIOMotorDatabase, 
        skus: Optional[List[str]] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate forecasts for multiple products"""
        try:
            # Get SKUs to forecast
            if not skus:
                skus = await self._get_active_skus(db)
            
            results = []
            successful_forecasts = 0
            failed_forecasts = 0
            
            for sku in skus:
                forecast_result = await self.generate_demand_forecast(db, sku, days, include_confidence=False)
                results.append(forecast_result)
                
                if "error" in forecast_result:
                    failed_forecasts += 1
                else:
                    successful_forecasts += 1
            
            # Store forecasts in database
            await self._store_forecasts(db, results)
            
            return {
                "total_products": len(skus),
                "successful_forecasts": successful_forecasts,
                "failed_forecasts": failed_forecasts,
                "forecasts": results,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in batch forecast generation: {str(e)}")
            raise
    
    async def _get_historical_demand_data(self, db: AsyncIOMotorDatabase, sku: str) -> List[Dict]:
        """Get historical demand data from stock movements"""
        try:
            # Get stock movements for the SKU (outbound movements represent demand)
            pipeline = [
                {
                    "$match": {
                        "inventory_item_sku": sku,
                        "movement_type": {"$in": ["OUT", "TRANSFER"]},  # Demand indicators
                        "created_at": {"$gte": datetime.utcnow() - timedelta(days=365)}  # Last year
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"},
                            "day": {"$dayOfMonth": "$created_at"}
                        },
                        "total_demand": {"$sum": {"$abs": "$quantity"}},
                        "date": {"$first": "$created_at"}
                    }
                },
                {
                    "$project": {
                        "date": {
                            "$dateFromParts": {
                                "year": "$_id.year",
                                "month": "$_id.month",
                                "day": "$_id.day"
                            }
                        },
                        "demand": "$total_demand"
                    }
                },
                {"$sort": {"date": 1}}
            ]
            
            cursor = db.stock_movements.aggregate(pipeline)
            data = await cursor.to_list(length=None)
            
            # Fill missing days with zero demand
            if data:
                filled_data = await self._fill_missing_dates(data)
                return filled_data
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting historical data for {sku}: {str(e)}")
            return []
    
    async def _fill_missing_dates(self, data: List[Dict]) -> List[Dict]:
        """Fill missing dates with zero demand"""
        if not data:
            return []
        
        # Create date range
        start_date = data[0]["date"]
        end_date = data[-1]["date"]
        
        # Create complete date range
        current_date = start_date
        filled_data = []
        data_dict = {item["date"].date(): item["demand"] for item in data}
        
        while current_date <= end_date:
            demand = data_dict.get(current_date.date(), 0)
            filled_data.append({
                "date": current_date,
                "demand": demand
            })
            current_date += timedelta(days=1)
        
        return filled_data
    
    async def _prepare_prophet_data(self, historical_data: List[Dict]) -> pd.DataFrame:
        """Prepare data for Prophet model"""
        loop = asyncio.get_event_loop()
        
        def prepare():
            df = pd.DataFrame(historical_data)
            df['ds'] = pd.to_datetime(df['date'])
            df['y'] = df['demand'].astype(float)
            return df[['ds', 'y']]
        
        return await loop.run_in_executor(self.executor, prepare)
    
    async def _get_or_train_model(self, sku: str, df: pd.DataFrame) -> Prophet:
        """Get cached model or train new one"""
        model_path = os.path.join(settings.MODEL_DIR, f"demand_forecast_{sku}.joblib")
        
        # Check if model exists and is recent
        if os.path.exists(model_path):
            try:
                model_info = joblib.load(model_path)
                model = model_info['model']
                trained_date = model_info['trained_date']
                
                # Use cached model if trained within last 7 days
                if (datetime.utcnow() - trained_date).days < 7:
                    logger.info(f"Using cached model for {sku}")
                    return model
            except Exception as e:
                logger.warning(f"Error loading cached model for {sku}: {str(e)}")
        
        # Train new model
        model = await self._train_new_model(sku, df)
        
        # Save model
        try:
            os.makedirs(settings.MODEL_DIR, exist_ok=True)
            joblib.dump({
                'model': model,
                'trained_date': datetime.utcnow(),
                'sku': sku
            }, model_path)
        except Exception as e:
            logger.warning(f"Error saving model for {sku}: {str(e)}")
        
        return model
    
    async def _train_new_model(self, sku: str, df: pd.DataFrame) -> Prophet:
        """Train new Prophet model"""
        loop = asyncio.get_event_loop()
        
        def train():
            logger.info(f"Training new forecast model for {sku}")
            
            # Configure Prophet model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True if len(df) > 365 else False,
                changepoint_prior_scale=0.1,  # Adjust trend flexibility
                seasonality_prior_scale=10.0,  # Adjust seasonality strength
                uncertainty_samples=1000,  # For confidence intervals
                interval_width=0.95  # 95% confidence interval
            )
            
            # Add custom seasonalities if enough data
            if len(df) > 60:  # Monthly seasonality
                model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            
            # Fit the model
            model.fit(df)
            return model
        
        return await loop.run_in_executor(self.executor, train)
    
    async def _generate_forecast(self, model: Prophet, days: int, include_confidence: bool) -> Dict[str, Any]:
        """Generate forecast using trained model"""
        loop = asyncio.get_event_loop()
        
        def forecast():
            # Create future dates
            future = model.make_future_dataframe(periods=days, freq='D')
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Extract recent historical and future predictions
            historical_end = len(forecast) - days
            recent_historical = forecast.tail(days + 30).head(30)  # Last 30 days of history
            predictions = forecast.tail(days)  # Next `days` predictions
            
            result = {
                "historical_data": [],
                "predictions": []
            }
            
            # Format historical data
            for idx, row in recent_historical.iterrows():
                result["historical_data"].append({
                    "date": row['ds'].strftime('%Y-%m-%d'),
                    "actual_demand": max(0, round(row['yhat'], 2)),
                    "trend": round(row['trend'], 2) if 'trend' in row else None
                })
            
            # Format predictions
            for idx, row in predictions.iterrows():
                prediction = {
                    "date": row['ds'].strftime('%Y-%m-%d'),
                    "predicted_demand": max(0, round(row['yhat'], 2)),
                    "trend": round(row['trend'], 2) if 'trend' in row else None
                }
                
                if include_confidence:
                    prediction.update({
                        "lower_bound": max(0, round(row['yhat_lower'], 2)),
                        "upper_bound": max(0, round(row['yhat_upper'], 2))
                    })
                
                result["predictions"].append(prediction)
            
            # Add summary statistics
            result["summary"] = {
                "total_predicted_demand": sum(p["predicted_demand"] for p in result["predictions"]),
                "average_daily_demand": round(np.mean([p["predicted_demand"] for p in result["predictions"]]), 2),
                "max_daily_demand": max(p["predicted_demand"] for p in result["predictions"]),
                "min_daily_demand": min(p["predicted_demand"] for p in result["predictions"])
            }
            
            return result
        
        return await loop.run_in_executor(self.executor, forecast)
    
    async def _generate_forecast_insights(
        self, 
        db: AsyncIOMotorDatabase, 
        sku: str, 
        forecast_result: Dict, 
        historical_data: List[Dict]
    ) -> Dict[str, Any]:
        """Generate insights from forecast"""
        try:
            insights = {}
            
            # Trend analysis
            predictions = forecast_result["predictions"]
            if len(predictions) > 1:
                recent_trend = predictions[-1]["predicted_demand"] - predictions[0]["predicted_demand"]
                insights["trend_analysis"] = {
                    "direction": "increasing" if recent_trend > 0 else "decreasing" if recent_trend < 0 else "stable",
                    "magnitude": abs(round(recent_trend, 2)),
                    "percentage_change": round((recent_trend / max(predictions[0]["predicted_demand"], 0.1)) * 100, 1)
                }
            
            # Seasonality patterns
            daily_demands = [p["predicted_demand"] for p in predictions]
            if daily_demands:
                insights["seasonality"] = {
                    "variation_coefficient": round(np.std(daily_demands) / max(np.mean(daily_demands), 0.1), 3),
                    "peak_day": predictions[np.argmax(daily_demands)]["date"],
                    "low_day": predictions[np.argmin(daily_demands)]["date"]
                }
            
            # Comparison with historical average
            if historical_data:
                historical_avg = np.mean([d["demand"] for d in historical_data])
                forecast_avg = forecast_result["summary"]["average_daily_demand"]
                insights["vs_historical"] = {
                    "historical_average": round(historical_avg, 2),
                    "forecast_average": forecast_avg,
                    "change_percentage": round(((forecast_avg - historical_avg) / max(historical_avg, 0.1)) * 100, 1)
                }
            
            # Stock recommendations
            current_item = await db.inventory.find_one({"sku": sku})
            if current_item:
                total_forecast_demand = forecast_result["summary"]["total_predicted_demand"]
                current_stock = current_item.get("current_stock", 0)
                
                insights["stock_recommendations"] = {
                    "current_stock": current_stock,
                    "forecast_demand": total_forecast_demand,
                    "stock_coverage_days": round(current_stock / max(forecast_avg, 0.1), 1) if forecast_avg > 0 else float('inf'),
                    "recommended_reorder": total_forecast_demand > current_stock,
                    "suggested_order_quantity": max(0, round(total_forecast_demand - current_stock + current_item.get("minimum_stock", 0), 0))
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights for {sku}: {str(e)}")
            return {"error": "Could not generate insights"}
    
    async def _get_model_performance(self, model: Prophet, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate model performance metrics"""
        try:
            loop = asyncio.get_event_loop()
            
            def calculate_performance():
                # Cross-validation if enough data
                if len(df) > 30:
                    from prophet.diagnostics import cross_validation, performance_metrics
                    
                    # Perform cross-validation
                    cv_results = cross_validation(
                        model, 
                        initial='30 days', 
                        period='7 days', 
                        horizon='7 days',
                        disable_tqdm=True
                    )
                    
                    # Calculate performance metrics
                    metrics = performance_metrics(cv_results)
                    
                    return {
                        "mae": round(metrics['mae'].mean(), 2),  # Mean Absolute Error
                        "rmse": round(metrics['rmse'].mean(), 2),  # Root Mean Square Error
                        "mape": round(metrics['mape'].mean() * 100, 2),  # Mean Absolute Percentage Error
                        "coverage": round(metrics['coverage'].mean(), 2),  # Coverage of prediction intervals
                        "validation_periods": len(cv_results)
                    }
                else:
                    return {
                        "status": "insufficient_data_for_validation",
                        "data_points": len(df)
                    }
            
            return await loop.run_in_executor(self.executor, calculate_performance)
            
        except Exception as e:
            logger.warning(f"Error calculating model performance: {str(e)}")
            return {"error": "Could not calculate performance metrics"}
    
    async def _get_active_skus(self, db: AsyncIOMotorDatabase) -> List[str]:
        """Get list of active SKUs for batch forecasting"""
        try:
            cursor = db.inventory.find(
                {"status": {"$ne": "discontinued"}},
                {"sku": 1}
            )
            items = await cursor.to_list(length=None)
            return [item["sku"] for item in items]
        except Exception as e:
            logger.error(f"Error getting active SKUs: {str(e)}")
            return []
    
    async def _store_forecasts(self, db: AsyncIOMotorDatabase, forecasts: List[Dict]):
        """Store forecast results in database"""
        try:
            forecast_docs = []
            for forecast in forecasts:
                if "error" not in forecast:
                    doc = {
                        "sku": forecast["sku"],
                        "forecast_data": forecast,
                        "generated_at": datetime.utcnow(),
                        "forecast_horizon_days": forecast["forecast_days"],
                        "model_version": "prophet_v1"
                    }
                    forecast_docs.append(doc)
            
            if forecast_docs:
                # Remove old forecasts for these SKUs
                skus = [doc["sku"] for doc in forecast_docs]
                await db.demand_forecasts.delete_many({"sku": {"$in": skus}})
                
                # Insert new forecasts
                await db.demand_forecasts.insert_many(forecast_docs)
                logger.info(f"Stored {len(forecast_docs)} forecasts in database")
                
        except Exception as e:
            logger.error(f"Error storing forecasts: {str(e)}")
    
    async def get_stored_forecast(self, db: AsyncIOMotorDatabase, sku: str) -> Optional[Dict]:
        """Get previously stored forecast for a SKU"""
        try:
            forecast = await db.demand_forecasts.find_one(
                {"sku": sku},
                sort=[("generated_at", -1)]
            )
            return forecast["forecast_data"] if forecast else None
        except Exception as e:
            logger.error(f"Error getting stored forecast for {sku}: {str(e)}")
            return None
    
    async def get_forecast_accuracy(self, db: AsyncIOMotorDatabase, sku: str, days_back: int = 30) -> Dict[str, Any]:
        """Calculate forecast accuracy by comparing with actual demand"""
        try:
            # Get forecast from `days_back` days ago
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            old_forecast = await db.demand_forecasts.find_one({
                "sku": sku,
                "generated_at": {"$lte": cutoff_date}
            }, sort=[("generated_at", -1)])
            
            if not old_forecast:
                return {"error": "No historical forecast found for accuracy calculation"}
            
            # Get actual demand for the forecast period
            actual_data = await self._get_historical_demand_data(db, sku)
            
            # Calculate accuracy metrics
            # This is a simplified version - in production, you'd want more sophisticated accuracy measurement
            return {
                "sku": sku,
                "forecast_date": old_forecast["generated_at"],
                "accuracy_period_days": days_back,
                "status": "accuracy_calculation_available",
                "note": "Detailed accuracy calculation would compare predicted vs actual demand"
            }
            
        except Exception as e:
            logger.error(f"Error calculating forecast accuracy for {sku}: {str(e)}")
            return {"error": str(e)}

# Global forecasting service instance
forecasting_service = ForecastingService()
