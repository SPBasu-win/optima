"""
CSV ML Service for Supply Chain Management

This service provides comprehensive ML functionality for CSV data:
1. CSV file processing and validation
2. Demand forecasting with historical CSV data
3. Inventory optimization ML models
4. Sales pattern analysis
5. Automated data insights and recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from prophet import Prophet
import joblib
import os

logger = logging.getLogger(__name__)

class CSVMLService:
    """Comprehensive ML service for CSV data processing"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.models_cache = {}
        self.scalers_cache = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize the CSV ML service"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing CSV ML Service...")
            # Create models directory if it doesn't exist
            os.makedirs("models", exist_ok=True)
            self._initialized = True
            logger.info("CSV ML Service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing CSV ML Service: {e}")
            raise
    
    # ===== CSV DATA PROCESSING =====
    
    async def process_csv_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process uploaded CSV file and prepare for ML analysis"""
        try:
            # Detect encoding
            encoding = self._detect_encoding(file_content)
            
            # Read CSV
            df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
            
            # Basic validation
            if df.empty:
                raise ValueError("CSV file is empty")
            
            # Analyze data structure
            analysis = await self._analyze_csv_structure(df)
            
            # Clean and standardize data
            cleaned_df = await self._clean_csv_data(df)
            
            # Detect data patterns
            patterns = await self._detect_data_patterns(cleaned_df)
            
            return {
                "success": True,
                "filename": filename,
                "original_shape": df.shape,
                "cleaned_shape": cleaned_df.shape,
                "data_analysis": analysis,
                "data_patterns": patterns,
                "cleaned_data": cleaned_df.to_dict('records'),
                "columns": cleaned_df.columns.tolist(),
                "preview": cleaned_df.head(10).to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {e}")
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }
    
    def _detect_encoding(self, file_content: bytes) -> str:
        """Detect file encoding"""
        try:
            import chardet
            result = chardet.detect(file_content)
            return result['encoding'] or 'utf-8'
        except Exception:
            return 'utf-8'
    
    async def _analyze_csv_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze CSV data structure"""
        loop = asyncio.get_event_loop()
        
        def analyze():
            analysis = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "column_types": {},
                "missing_data": {},
                "data_quality_score": 0,
                "recommended_ml_tasks": []
            }
            
            # Analyze each column
            for col in df.columns:
                col_type = str(df[col].dtype)
                missing_pct = (df[col].isnull().sum() / len(df)) * 100
                
                analysis["column_types"][col] = {
                    "type": col_type,
                    "missing_percentage": round(missing_pct, 2),
                    "unique_values": df[col].nunique(),
                    "sample_values": df[col].dropna().head(5).tolist()
                }
                
                analysis["missing_data"][col] = missing_pct
            
            # Calculate data quality score
            avg_missing = np.mean(list(analysis["missing_data"].values()))
            analysis["data_quality_score"] = max(0, 100 - avg_missing)
            
            # Recommend ML tasks based on data structure
            analysis["recommended_ml_tasks"] = self._recommend_ml_tasks(df)
            
            return analysis
        
        return await loop.run_in_executor(self.executor, analyze)
    
    def _recommend_ml_tasks(self, df: pd.DataFrame) -> List[str]:
        """Recommend ML tasks based on data structure"""
        recommendations = []
        
        # Check for time series data
        date_cols = df.select_dtypes(include=['datetime64', 'object']).columns
        for col in date_cols:
            try:
                pd.to_datetime(df[col], errors='raise')
                recommendations.append("demand_forecasting")
                recommendations.append("time_series_analysis")
                break
            except:
                pass
        
        # Check for inventory-related columns
        inventory_keywords = ['stock', 'quantity', 'inventory', 'units', 'sku', 'product']
        if any(keyword in col.lower() for col in df.columns for keyword in inventory_keywords):
            recommendations.append("inventory_optimization")
            recommendations.append("stock_analysis")
        
        # Check for sales/demand data
        sales_keywords = ['sales', 'demand', 'sold', 'revenue', 'price']
        if any(keyword in col.lower() for col in df.columns for keyword in sales_keywords):
            recommendations.append("sales_forecasting")
            recommendations.append("demand_prediction")
        
        # Check for supplier/logistics data
        logistics_keywords = ['supplier', 'vendor', 'shipping', 'delivery', 'logistics']
        if any(keyword in col.lower() for col in df.columns for keyword in logistics_keywords):
            recommendations.append("supplier_analysis")
            recommendations.append("logistics_optimization")
        
        return list(set(recommendations))  # Remove duplicates
    
    async def _clean_csv_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize CSV data"""
        loop = asyncio.get_event_loop()
        
        def clean():
            cleaned_df = df.copy()
            
            # Handle missing values
            for col in cleaned_df.columns:
                if cleaned_df[col].dtype == 'object':
                    cleaned_df[col] = cleaned_df[col].fillna('Unknown')
                else:
                    cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
            
            # Standardize column names
            cleaned_df.columns = [col.lower().replace(' ', '_').replace('-', '_') 
                                 for col in cleaned_df.columns]
            
            # Convert date columns
            for col in cleaned_df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    try:
                        cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
                    except:
                        pass
            
            # Convert numeric columns
            numeric_keywords = ['price', 'cost', 'quantity', 'stock', 'amount', 'value']
            for col in cleaned_df.columns:
                if any(keyword in col.lower() for keyword in numeric_keywords):
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)
            
            return cleaned_df
        
        return await loop.run_in_executor(self.executor, clean)
    
    async def _detect_data_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect patterns in the data"""
        loop = asyncio.get_event_loop()
        
        def detect():
            patterns = {
                "seasonality": {},
                "trends": {},
                "correlations": {},
                "outliers": {},
                "clusters": {}
            }
            
            # Detect time-based patterns
            for col in df.columns:
                if df[col].dtype == 'datetime64[ns]':
                    patterns["seasonality"][col] = self._analyze_seasonality(df, col)
            
            # Detect trends in numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if len(df[col].unique()) > 10:  # Skip categorical numeric columns
                    patterns["trends"][col] = self._analyze_trend(df[col])
            
            # Correlation analysis
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr()
                patterns["correlations"] = self._find_strong_correlations(corr_matrix)
            
            # Outlier detection
            for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
                patterns["outliers"][col] = self._detect_outliers(df[col])
            
            return patterns
        
        return await loop.run_in_executor(self.executor, detect)
    
    # ===== DEMAND FORECASTING WITH CSV =====
    
    async def forecast_demand_from_csv(
        self, 
        df: pd.DataFrame, 
        date_col: str, 
        demand_col: str,
        product_col: Optional[str] = None,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Generate demand forecast from CSV data"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Prepare data for forecasting
            forecast_data = await self._prepare_forecast_data(df, date_col, demand_col, product_col)
            
            results = {}
            
            if product_col and product_col in df.columns:
                # Forecast for each product
                products = df[product_col].unique()[:10]  # Limit to 10 products
                
                for product in products:
                    product_data = forecast_data[forecast_data[product_col] == product]
                    if len(product_data) >= 10:  # Minimum data required
                        forecast_result = await self._generate_prophet_forecast(
                            product_data, date_col, demand_col, forecast_days
                        )
                        results[str(product)] = forecast_result
            else:
                # Single product/aggregate forecast
                forecast_result = await self._generate_prophet_forecast(
                    forecast_data, date_col, demand_col, forecast_days
                )
                results["aggregate"] = forecast_result
            
            return {
                "success": True,
                "forecast_results": results,
                "data_points_used": len(forecast_data),
                "forecast_horizon_days": forecast_days,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in demand forecasting: {e}")
            return {
                "success": False,
                "error": str(e),
                "forecast_horizon_days": forecast_days
            }
    
    async def _prepare_forecast_data(
        self, 
        df: pd.DataFrame, 
        date_col: str, 
        demand_col: str,
        product_col: Optional[str]
    ) -> pd.DataFrame:
        """Prepare data for forecasting"""
        loop = asyncio.get_event_loop()
        
        def prepare():
            # Ensure date column is datetime
            df[date_col] = pd.to_datetime(df[date_col])
            
            # Ensure demand column is numeric
            df[demand_col] = pd.to_numeric(df[demand_col], errors='coerce').fillna(0)
            
            # Sort by date
            df_sorted = df.sort_values(date_col)
            
            # Group by date (and product if specified) and sum demand
            group_cols = [date_col]
            if product_col:
                group_cols.append(product_col)
            
            aggregated = df_sorted.groupby(group_cols)[demand_col].sum().reset_index()
            
            return aggregated
        
        return await loop.run_in_executor(self.executor, prepare)
    
    async def _generate_prophet_forecast(
        self, 
        data: pd.DataFrame, 
        date_col: str, 
        demand_col: str,
        forecast_days: int
    ) -> Dict[str, Any]:
        """Generate Prophet-based forecast"""
        loop = asyncio.get_event_loop()
        
        def forecast():
            try:
                # Prepare data for Prophet
                prophet_data = pd.DataFrame({
                    'ds': data[date_col],
                    'y': data[demand_col]
                })
                
                # Initialize Prophet model
                model = Prophet(
                    daily_seasonality=True,
                    weekly_seasonality=True,
                    yearly_seasonality=len(prophet_data) > 365,
                    changepoint_prior_scale=0.05,
                    seasonality_prior_scale=10
                )
                
                # Fit model
                model.fit(prophet_data)
                
                # Create future dataframe
                future = model.make_future_dataframe(periods=forecast_days)
                
                # Generate forecast
                forecast = model.predict(future)
                
                # Extract predictions for future dates
                future_forecast = forecast.tail(forecast_days)
                
                # Format results
                predictions = []
                for idx, row in future_forecast.iterrows():
                    predictions.append({
                        "date": row['ds'].strftime('%Y-%m-%d'),
                        "predicted_demand": max(0, round(row['yhat'], 2)),
                        "lower_bound": max(0, round(row['yhat_lower'], 2)),
                        "upper_bound": max(0, round(row['yhat_upper'], 2)),
                        "trend": round(row['trend'], 2) if 'trend' in row else None
                    })
                
                # Calculate summary statistics
                total_predicted = sum(p["predicted_demand"] for p in predictions)
                avg_predicted = total_predicted / len(predictions) if predictions else 0
                
                # Model performance (simplified)
                historical_actual = prophet_data['y'].values
                historical_predicted = forecast.head(len(historical_actual))['yhat'].values
                mae = mean_absolute_error(historical_actual, historical_predicted)
                rmse = np.sqrt(mean_squared_error(historical_actual, historical_predicted))
                
                return {
                    "predictions": predictions,
                    "summary": {
                        "total_predicted_demand": round(total_predicted, 2),
                        "average_daily_demand": round(avg_predicted, 2),
                        "forecast_period_days": forecast_days
                    },
                    "model_performance": {
                        "mae": round(mae, 2),
                        "rmse": round(rmse, 2),
                        "data_points": len(historical_actual)
                    },
                    "confidence_interval": "80%"
                }
                
            except Exception as e:
                logger.error(f"Prophet forecasting error: {e}")
                # Fallback to simple trend-based forecast
                return self._simple_trend_forecast(data, demand_col, forecast_days)
        
        return await loop.run_in_executor(self.executor, forecast)
    
    def _simple_trend_forecast(self, data: pd.DataFrame, demand_col: str, forecast_days: int) -> Dict[str, Any]:
        """Simple trend-based forecast as fallback"""
        try:
            recent_data = data[demand_col].tail(30).values
            trend = np.polyfit(range(len(recent_data)), recent_data, 1)[0]
            base_demand = recent_data.mean()
            
            predictions = []
            for day in range(1, forecast_days + 1):
                predicted = max(0, base_demand + (trend * day) + np.random.normal(0, base_demand * 0.1))
                future_date = datetime.now() + timedelta(days=day)
                predictions.append({
                    "date": future_date.strftime('%Y-%m-%d'),
                    "predicted_demand": round(predicted, 2),
                    "lower_bound": round(predicted * 0.8, 2),
                    "upper_bound": round(predicted * 1.2, 2),
                    "trend": round(trend, 2)
                })
            
            total_predicted = sum(p["predicted_demand"] for p in predictions)
            
            return {
                "predictions": predictions,
                "summary": {
                    "total_predicted_demand": round(total_predicted, 2),
                    "average_daily_demand": round(total_predicted / forecast_days, 2),
                    "forecast_period_days": forecast_days
                },
                "model_performance": {
                    "method": "simple_trend",
                    "data_points": len(recent_data)
                },
                "confidence_interval": "Estimated"
            }
        except Exception as e:
            logger.error(f"Simple trend forecast error: {e}")
            return {"error": "Forecast generation failed"}
    
    # ===== INVENTORY OPTIMIZATION WITH CSV =====
    
    async def optimize_inventory_from_csv(
        self, 
        df: pd.DataFrame,
        product_col: str,
        stock_col: str,
        sales_col: Optional[str] = None,
        cost_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """Optimize inventory based on CSV data"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Prepare inventory data
            inventory_analysis = await self._analyze_inventory_data(df, product_col, stock_col, sales_col, cost_col)
            
            # Generate optimization recommendations
            optimization_results = await self._generate_inventory_optimization(inventory_analysis)
            
            # ABC Analysis
            abc_analysis = await self._perform_abc_analysis(df, product_col, sales_col, cost_col)
            
            # Stock level recommendations
            stock_recommendations = await self._generate_stock_recommendations(
                inventory_analysis, optimization_results
            )
            
            return {
                "success": True,
                "inventory_analysis": inventory_analysis,
                "optimization_results": optimization_results,
                "abc_analysis": abc_analysis,
                "stock_recommendations": stock_recommendations,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in inventory optimization: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_inventory_data(
        self, 
        df: pd.DataFrame, 
        product_col: str, 
        stock_col: str,
        sales_col: Optional[str],
        cost_col: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze inventory data"""
        loop = asyncio.get_event_loop()
        
        def analyze():
            analysis = {
                "total_products": df[product_col].nunique(),
                "total_stock_value": 0,
                "average_stock_level": df[stock_col].mean(),
                "stock_distribution": {},
                "products_analysis": []
            }
            
            # Stock level distribution
            analysis["stock_distribution"] = {
                "low_stock": len(df[df[stock_col] < df[stock_col].quantile(0.25)]),
                "medium_stock": len(df[(df[stock_col] >= df[stock_col].quantile(0.25)) & 
                                     (df[stock_col] <= df[stock_col].quantile(0.75))]),
                "high_stock": len(df[df[stock_col] > df[stock_col].quantile(0.75)])
            }
            
            # Per-product analysis
            for product in df[product_col].unique()[:50]:  # Limit to 50 products
                product_data = df[df[product_col] == product]
                
                product_analysis = {
                    "product": str(product),
                    "current_stock": product_data[stock_col].sum(),
                    "stock_variance": product_data[stock_col].var() if len(product_data) > 1 else 0
                }
                
                if sales_col and sales_col in df.columns:
                    product_analysis["total_sales"] = product_data[sales_col].sum()
                    product_analysis["avg_sales"] = product_data[sales_col].mean()
                
                if cost_col and cost_col in df.columns:
                    product_analysis["total_value"] = (
                        product_data[stock_col] * product_data[cost_col]
                    ).sum()
                    analysis["total_stock_value"] += product_analysis["total_value"]
                
                analysis["products_analysis"].append(product_analysis)
            
            return analysis
        
        return await loop.run_in_executor(self.executor, analyze)
    
    async def _generate_inventory_optimization(self, inventory_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate inventory optimization recommendations"""
        loop = asyncio.get_event_loop()
        
        def optimize():
            optimization = {
                "overall_recommendations": [],
                "product_recommendations": [],
                "cost_savings_potential": 0,
                "risk_assessment": {}
            }
            
            # Overall recommendations
            total_products = inventory_analysis["total_products"]
            avg_stock = inventory_analysis["average_stock_level"]
            
            if avg_stock > 100:
                optimization["overall_recommendations"].append(
                    "Consider reducing overall stock levels - high average inventory detected"
                )
            
            stock_dist = inventory_analysis["stock_distribution"]
            if stock_dist["high_stock"] > total_products * 0.3:
                optimization["overall_recommendations"].append(
                    "30%+ of products have high stock levels - review demand patterns"
                )
            
            # Per-product recommendations
            for product_data in inventory_analysis["products_analysis"][:20]:
                product_rec = {
                    "product": product_data["product"],
                    "recommendations": [],
                    "priority": "medium"
                }
                
                current_stock = product_data["current_stock"]
                
                if current_stock > avg_stock * 2:
                    product_rec["recommendations"].append("Reduce stock level - overstocked")
                    product_rec["priority"] = "high"
                elif current_stock < avg_stock * 0.3:
                    product_rec["recommendations"].append("Increase stock level - understocked")
                    product_rec["priority"] = "high"
                
                if "total_sales" in product_data:
                    sales_to_stock_ratio = product_data["total_sales"] / max(current_stock, 1)
                    if sales_to_stock_ratio > 2:
                        product_rec["recommendations"].append("High demand product - ensure adequate stock")
                    elif sales_to_stock_ratio < 0.1:
                        product_rec["recommendations"].append("Low demand product - consider reducing stock")
                
                if product_rec["recommendations"]:
                    optimization["product_recommendations"].append(product_rec)
            
            # Risk assessment
            high_stock_count = stock_dist["high_stock"]
            low_stock_count = stock_dist["low_stock"]
            
            optimization["risk_assessment"] = {
                "overstock_risk": "High" if high_stock_count > total_products * 0.4 else "Medium",
                "stockout_risk": "High" if low_stock_count > total_products * 0.3 else "Low",
                "inventory_balance": "Good" if 0.2 <= high_stock_count/total_products <= 0.3 else "Needs attention"
            }
            
            return optimization
        
        return await loop.run_in_executor(self.executor, optimize)
    
    async def _perform_abc_analysis(
        self, 
        df: pd.DataFrame, 
        product_col: str,
        sales_col: Optional[str],
        cost_col: Optional[str]
    ) -> Dict[str, Any]:
        """Perform ABC analysis on inventory"""
        if not sales_col and not cost_col:
            return {"error": "Need sales or cost data for ABC analysis"}
        
        loop = asyncio.get_event_loop()
        
        def abc_analysis():
            # Calculate value (sales * cost or just sales)
            if sales_col and cost_col:
                df['abc_value'] = df[sales_col] * df[cost_col]
            elif sales_col:
                df['abc_value'] = df[sales_col]
            else:
                df['abc_value'] = df[cost_col]
            
            # Group by product and sum values
            product_values = df.groupby(product_col)['abc_value'].sum().sort_values(ascending=False)
            
            # Calculate cumulative percentage
            total_value = product_values.sum()
            cumulative_pct = (product_values.cumsum() / total_value * 100)
            
            # Classify products
            abc_classification = {}
            for product, cum_pct in cumulative_pct.items():
                if cum_pct <= 80:
                    abc_classification[product] = 'A'
                elif cum_pct <= 95:
                    abc_classification[product] = 'B'
                else:
                    abc_classification[product] = 'C'
            
            # Summary
            a_products = [p for p, c in abc_classification.items() if c == 'A']
            b_products = [p for p, c in abc_classification.items() if c == 'B']
            c_products = [p for p, c in abc_classification.items() if c == 'C']
            
            return {
                "classification": abc_classification,
                "summary": {
                    "A_products": {"count": len(a_products), "products": a_products[:10]},
                    "B_products": {"count": len(b_products), "products": b_products[:10]},
                    "C_products": {"count": len(c_products), "products": c_products[:10]}
                },
                "recommendations": {
                    "A_products": "High priority - tight control, frequent monitoring",
                    "B_products": "Medium priority - periodic review and control",
                    "C_products": "Low priority - simple controls, bulk management"
                }
            }
        
        return await loop.run_in_executor(self.executor, abc_analysis)
    
    async def _generate_stock_recommendations(
        self, 
        inventory_analysis: Dict[str, Any],
        optimization_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate specific stock level recommendations"""
        loop = asyncio.get_event_loop()
        
        def generate_recommendations():
            recommendations = {
                "reorder_recommendations": [],
                "excess_stock_alerts": [],
                "critical_items": [],
                "summary": {}
            }
            
            avg_stock = inventory_analysis["average_stock_level"]
            
            for product_data in inventory_analysis["products_analysis"][:30]:
                product = product_data["product"]
                current_stock = product_data["current_stock"]
                
                # Reorder recommendations
                if current_stock < avg_stock * 0.2:
                    recommendations["reorder_recommendations"].append({
                        "product": product,
                        "current_stock": current_stock,
                        "recommended_reorder_point": round(avg_stock * 0.3, 0),
                        "suggested_order_quantity": round(avg_stock * 0.5, 0),
                        "urgency": "high"
                    })
                
                # Excess stock alerts
                if current_stock > avg_stock * 3:
                    recommendations["excess_stock_alerts"].append({
                        "product": product,
                        "current_stock": current_stock,
                        "recommended_stock_level": round(avg_stock * 1.5, 0),
                        "excess_quantity": round(current_stock - avg_stock * 1.5, 0)
                    })
                
                # Critical items (very low stock)
                if current_stock < avg_stock * 0.1:
                    recommendations["critical_items"].append({
                        "product": product,
                        "current_stock": current_stock,
                        "risk_level": "critical",
                        "immediate_action_required": True
                    })
            
            # Summary
            recommendations["summary"] = {
                "products_to_reorder": len(recommendations["reorder_recommendations"]),
                "excess_stock_items": len(recommendations["excess_stock_alerts"]),
                "critical_items": len(recommendations["critical_items"]),
                "total_products_analyzed": len(inventory_analysis["products_analysis"])
            }
            
            return recommendations
        
        return await loop.run_in_executor(self.executor, generate_recommendations)
    
    # ===== UTILITY METHODS =====
    
    def _analyze_seasonality(self, df: pd.DataFrame, date_col: str) -> Dict[str, Any]:
        """Analyze seasonality patterns in time series data"""
        try:
            df_sorted = df.sort_values(date_col)
            df_sorted['month'] = df_sorted[date_col].dt.month
            df_sorted['day_of_week'] = df_sorted[date_col].dt.dayofweek
            
            return {
                "monthly_pattern_detected": len(df_sorted['month'].unique()) > 6,
                "weekly_pattern_detected": len(df_sorted['day_of_week'].unique()) == 7,
                "data_span_days": (df_sorted[date_col].max() - df_sorted[date_col].min()).days
            }
        except Exception:
            return {"error": "Could not analyze seasonality"}
    
    def _analyze_trend(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze trend in numeric series"""
        try:
            x = np.arange(len(series))
            y = series.values
            
            # Linear regression for trend
            slope, intercept = np.polyfit(x, y, 1)
            
            return {
                "trend_direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                "trend_strength": abs(slope),
                "r_squared": r2_score(y, slope * x + intercept) if len(y) > 1 else 0
            }
        except Exception:
            return {"error": "Could not analyze trend"}
    
    def _find_strong_correlations(self, corr_matrix: pd.DataFrame, threshold: float = 0.7) -> Dict[str, Any]:
        """Find strong correlations in correlation matrix"""
        try:
            strong_correlations = []
            
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > threshold:
                        strong_correlations.append({
                            "variable_1": corr_matrix.columns[i],
                            "variable_2": corr_matrix.columns[j],
                            "correlation": round(corr_value, 3),
                            "strength": "strong" if abs(corr_value) > 0.8 else "moderate"
                        })
            
            return {
                "strong_correlations": strong_correlations,
                "correlation_count": len(strong_correlations)
            }
        except Exception:
            return {"error": "Could not analyze correlations"}
    
    def _detect_outliers(self, series: pd.Series) -> Dict[str, Any]:
        """Detect outliers using IQR method"""
        try:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = series[(series < lower_bound) | (series > upper_bound)]
            
            return {
                "outlier_count": len(outliers),
                "outlier_percentage": round((len(outliers) / len(series)) * 100, 2),
                "outlier_bounds": {"lower": round(lower_bound, 2), "upper": round(upper_bound, 2)},
                "sample_outliers": outliers.head(5).tolist()
            }
        except Exception:
            return {"error": "Could not detect outliers"}

# Global service instance
csv_ml_service = CSVMLService()

async def initialize_csv_ml_service():
    """Initialize CSV ML service"""
    await csv_ml_service.initialize()
