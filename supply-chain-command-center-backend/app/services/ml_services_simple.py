"""
Simplified ML Services for Development/Testing

This is a lightweight version that doesn't require heavy ML dependencies
"""

import re
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SimpleParaphraseService:
    """Simple text cleaning service without ML dependencies"""
    
    def __init__(self):
        self._initialized = True
    
    async def initialize(self):
        """Initialize service - no-op for simple version"""
        pass
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text data without ML"""
        if not text or pd.isna(text):
            return ""
        
        # Convert to string and strip
        text = str(text).strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep alphanumeric and basic punctuation
        text = re.sub(r'[^\w\s\-.,()&$]', '', text)
        
        # Remove $ signs from non-price fields and clean prices
        if '$' in text:
            # If it looks like a price, keep the $ and format properly
            price_match = re.match(r'^\$?(\d+\.?\d*)$', text)
            if price_match:
                return price_match.group(1)  # Remove $ for numeric processing
        
        # Capitalize first letter of each word for product names
        if len(text) > 2 and not text.replace('.', '').isdigit():
            text = text.title()
        
        return text
    
    async def paraphrase_text(self, text: str, max_length: int = 50) -> str:
        """Simple text cleaning without paraphrasing"""
        return self.clean_text(text)
    
    async def clean_dataframe(self, df: pd.DataFrame, text_columns: List[str]) -> pd.DataFrame:
        """Clean text columns in a DataFrame"""
        cleaned_df = df.copy()
        
        for column in text_columns:
            if column in cleaned_df.columns:
                logger.info(f"Cleaning column: {column}")
                cleaned_df[column] = cleaned_df[column].apply(self.clean_text)
        
        return cleaned_df


class SimpleGemmaService:
    """Simple forecasting service without Gemma model"""
    
    def __init__(self):
        self._initialized = True
    
    async def initialize(self):
        """Initialize service - no-op for simple version"""
        pass
    
    async def generate_demand_forecast(
        self, 
        sku: str, 
        historical_data: List[Dict], 
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Generate simple demand forecast"""
        
        # Calculate base demand from historical data
        if historical_data:
            recent_demands = [record.get('demand', 50) for record in historical_data[-7:]]
            base_demand = np.mean(recent_demands) if recent_demands else 50
        else:
            base_demand = 50
        
        # Generate forecast with some variation
        forecast = []
        total_demand = 0
        
        np.random.seed(hash(sku) % 1000)  # Consistent randomness per SKU
        
        for day in range(1, forecast_days + 1):
            # Add some seasonality and randomness
            seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * day / 7)  # Weekly pattern
            trend_factor = 1 + 0.02 * (day / forecast_days)  # Slight upward trend
            random_factor = 1 + np.random.normal(0, 0.1)  # Random variation
            
            predicted = int(base_demand * seasonal_factor * trend_factor * random_factor)
            predicted = max(1, predicted)  # Ensure at least 1 unit
            forecast.append({"day": day, "predicted_demand": predicted})
            total_demand += predicted
        
        return {
            "forecast": forecast,
            "total_predicted_demand": int(total_demand),
            "confidence_level": 75,
            "insights": ["Stable demand pattern expected", "Based on historical analysis"],
            "model": "simple_forecast"
        }
    
    async def generate_cost_forecast(
        self, 
        sku: str, 
        historical_data: List[Dict], 
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Generate simple cost forecast"""
        
        # Calculate base cost from historical data
        if historical_data:
            recent_costs = [record.get('cost', 25.0) for record in historical_data[-7:]]
            base_cost = np.mean(recent_costs) if recent_costs else 25.0
        else:
            base_cost = 25.0
        
        # Generate cost forecast
        forecast = []
        total_cost = 0
        
        np.random.seed(hash(sku) % 1000)  # Consistent randomness per SKU
        
        for day in range(1, forecast_days + 1):
            # Add slight inflation and randomness
            inflation_factor = 1 + 0.001 * day  # Small daily inflation
            random_factor = 1 + np.random.normal(0, 0.05)  # Random variation
            
            predicted_cost = round(base_cost * inflation_factor * random_factor, 2)
            predicted_cost = max(0.01, predicted_cost)  # Minimum cost
            forecast.append({"day": day, "predicted_cost": predicted_cost})
            total_cost += predicted_cost
        
        return {
            "forecast": forecast,
            "total_predicted_cost": round(total_cost, 2),
            "trend": "slightly_increasing",
            "recommendations": ["Monitor for cost optimization opportunities", "Consider bulk purchasing"],
            "model": "simple_forecast"
        }


# Global service instances
paraphrase_service = SimpleParaphraseService()
gemma_service = SimpleGemmaService()

async def initialize_ml_services():
    """Initialize all ML services"""
    logger.info("Initializing simple ML services...")
    await paraphrase_service.initialize()
    await gemma_service.initialize()
    logger.info("Simple ML services initialized successfully")

# Utility functions for data processing
def detect_file_encoding(file_content: bytes) -> str:
    """Detect file encoding - simplified version"""
    # Try UTF-8 first, fallback to common encodings
    encodings = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            file_content.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    
    return 'utf-8'  # Default fallback

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names for inventory data"""
    column_mapping = {
        # Product identification
        'sku': 'sku', 'SKU': 'sku', 'product_id': 'sku', 'Product ID': 'sku',
        'item_code': 'sku', 'Item Code': 'sku', 'code': 'sku',
        
        # Product name
        'name': 'name', 'product_name': 'name', 'Product Name': 'name',
        'item_name': 'name', 'Item Name': 'name', 'description': 'name',
        'Description': 'name', 'product': 'name', 'Product': 'name',
        
        # Category
        'category': 'category', 'Category': 'category', 'type': 'category',
        'Type': 'category', 'group': 'category', 'Group': 'category',
        
        # Stock quantity
        'quantity': 'current_stock', 'Quantity': 'current_stock', 
        'stock': 'current_stock', 'Stock': 'current_stock',
        'current_stock': 'current_stock', 'Current Stock': 'current_stock',
        'qty': 'current_stock', 'QTY': 'current_stock',
        
        # Pricing
        'price': 'unit_price', 'Price': 'unit_price', 'unit_price': 'unit_price',
        'Unit Price': 'unit_price', 'cost': 'unit_price', 'Cost': 'unit_price',
        
        # Supplier
        'supplier': 'supplier', 'Supplier': 'supplier', 'vendor': 'supplier',
        'Vendor': 'supplier', 'supplier_name': 'supplier', 'Supplier Name': 'supplier',
        
        # Warehouse location
        'location': 'warehouse_location', 'Location': 'warehouse_location',
        'warehouse': 'warehouse_location', 'Warehouse': 'warehouse_location',
        'bin': 'warehouse_location', 'Bin': 'warehouse_location',
    }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Ensure required columns exist
    required_columns = ['sku', 'name', 'category', 'current_stock', 'unit_price', 'supplier']
    for col in required_columns:
        if col not in df.columns:
            if col == 'sku':
                df[col] = df.index.astype(str)  # Use index as SKU if missing
            elif col == 'name':
                df[col] = 'Unknown Product'
            elif col == 'category':
                df[col] = 'General'
            elif col == 'current_stock':
                df[col] = 0
            elif col == 'unit_price':
                df[col] = 0.0
            elif col == 'supplier':
                df[col] = 'Unknown Supplier'
    
    return df
