"""
ML Services for Supply Chain Command Center

This module provides services for:
1. Text paraphrasing and data cleaning using Hugging Face transformers
2. Demand and cost forecasting using Gemma model via Ollama
3. Data processing utilities for uploaded files
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ollama
from transformers import T5ForConditionalGeneration, T5Tokenizer
from sentence_transformers import SentenceTransformer
import torch
from app.core.config import settings

logger = logging.getLogger(__name__)

class ParaphraseService:
    """Service for text cleaning and paraphrasing using T5 model"""
    
    def __init__(self):
        self.model_name = "t5-small"
        self.model = None
        self.tokenizer = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the paraphrase model"""
        if self._initialized:
            return
            
        try:
            logger.info(f"Loading paraphrase model: {self.model_name}")
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
            self._initialized = True
            logger.info("Paraphrase model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading paraphrase model: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text data"""
        if not text or pd.isna(text):
            return ""
        
        # Convert to string and strip
        text = str(text).strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep alphanumeric and basic punctuation
        text = re.sub(r'[^\w\s\-.,()&]', '', text)
        
        # Capitalize first letter of each word for product names
        if len(text) > 0:
            text = text.title()
        
        return text
    
    async def paraphrase_text(self, text: str, max_length: int = 50) -> str:
        """Paraphrase text using T5 model for data cleaning"""
        if not self._initialized:
            await self.initialize()
        
        if not text or len(text.strip()) == 0:
            return ""
        
        try:
            # Prepare input for T5
            input_text = f"paraphrase: {text}"
            input_ids = self.tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
            
            # Generate paraphrase
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    max_length=max_length,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id
                )
            
            # Decode output
            paraphrased = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return self.clean_text(paraphrased)
            
        except Exception as e:
            logger.error(f"Error paraphrasing text: {e}")
            return self.clean_text(text)  # Fallback to basic cleaning
    
    async def clean_dataframe(self, df: pd.DataFrame, text_columns: List[str]) -> pd.DataFrame:
        """Clean text columns in a DataFrame"""
        cleaned_df = df.copy()
        
        for column in text_columns:
            if column in cleaned_df.columns:
                logger.info(f"Cleaning column: {column}")
                for idx, value in cleaned_df[column].items():
                    if pd.notna(value) and str(value).strip():
                        cleaned_df.loc[idx, column] = await self.paraphrase_text(str(value))
        
        return cleaned_df


class GemmaForecastingService:
    """Service for demand and cost forecasting using Gemma model via Ollama"""
    
    def __init__(self):
        self.model_name = "gemma:2b"  # Using Gemma 2B model
        self.client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Ollama client and ensure Gemma model is available"""
        if self._initialized:
            return
        
        try:
            # Check if Ollama is running and pull model if needed
            models = ollama.list()
            model_names = [model['name'] for model in models['models']]
            
            if self.model_name not in model_names:
                logger.info(f"Pulling Gemma model: {self.model_name}")
                ollama.pull(self.model_name)
            
            self._initialized = True
            logger.info("Gemma forecasting service initialized")
            
        except Exception as e:
            logger.error(f"Error initializing Gemma service: {e}")
            # Fallback to mock data for development
            self._initialized = True
            logger.warning("Using mock forecasting data - Ollama not available")
    
    def _format_historical_data(self, historical_data: List[Dict]) -> str:
        """Format historical data for Gemma model input"""
        if not historical_data:
            return "No historical data available."
        
        # Format data into a readable string
        formatted_lines = []
        for record in historical_data[-30:]:  # Last 30 records
            date = record.get('date', 'N/A')
            demand = record.get('demand', 0)
            cost = record.get('cost', 0)
            formatted_lines.append(f"Date: {date}, Demand: {demand} units, Cost: ${cost:.2f}")
        
        return "\n".join(formatted_lines)
    
    async def generate_demand_forecast(
        self, 
        sku: str, 
        historical_data: List[Dict], 
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Generate demand forecast using Gemma model"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Format historical data
            historical_context = self._format_historical_data(historical_data)
            
            # Create prompt for Gemma
            prompt = f"""
            Based on the following historical data for product SKU {sku}, predict the daily demand for the next {forecast_days} days.
            
            Historical Data:
            {historical_context}
            
            Please provide:
            1. Daily demand predictions for the next {forecast_days} days
            2. Total predicted demand
            3. Confidence level (as percentage)
            4. Key insights about demand patterns
            
            Format your response as JSON with the following structure:
            {{
                "forecast": [
                    {{"day": 1, "predicted_demand": 100}},
                    {{"day": 2, "predicted_demand": 105}}
                ],
                "total_predicted_demand": 3000,
                "confidence_level": 75,
                "insights": ["Stable demand pattern", "Slight upward trend"],
                "model": "gemma"
            }}
            """
            
            # Generate response using Ollama
            try:
                response = ollama.generate(model=self.model_name, prompt=prompt)
                result_text = response['response']
                
                # Try to parse JSON from response
                import json
                import re
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group())
                    return result_json
                
            except Exception as e:
                logger.warning(f"Ollama call failed, using fallback: {e}")
            
            # Fallback: Generate synthetic forecast
            return await self._generate_fallback_forecast(sku, historical_data, forecast_days)
            
        except Exception as e:
            logger.error(f"Error in demand forecasting: {e}")
            return await self._generate_fallback_forecast(sku, historical_data, forecast_days)
    
    async def generate_cost_forecast(
        self, 
        sku: str, 
        historical_data: List[Dict], 
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Generate cost forecast using Gemma model"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Format historical data
            historical_context = self._format_historical_data(historical_data)
            
            # Create prompt for Gemma
            prompt = f"""
            Based on the following historical cost data for product SKU {sku}, predict the daily costs for the next {forecast_days} days.
            
            Historical Data:
            {historical_context}
            
            Please provide:
            1. Daily cost predictions for the next {forecast_days} days
            2. Total predicted cost
            3. Cost trend analysis
            4. Recommendations for cost optimization
            
            Format your response as JSON with the following structure:
            {{
                "forecast": [
                    {{"day": 1, "predicted_cost": 25.50}},
                    {{"day": 2, "predicted_cost": 26.00}}
                ],
                "total_predicted_cost": 780.00,
                "trend": "increasing",
                "recommendations": ["Consider bulk purchasing", "Monitor supplier prices"],
                "model": "gemma"
            }}
            """
            
            try:
                response = ollama.generate(model=self.model_name, prompt=prompt)
                result_text = response['response']
                
                # Extract JSON from response
                import json
                import re
                
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group())
                    return result_json
                
            except Exception as e:
                logger.warning(f"Ollama call failed, using fallback: {e}")
            
            # Fallback: Generate synthetic cost forecast
            return await self._generate_fallback_cost_forecast(sku, historical_data, forecast_days)
            
        except Exception as e:
            logger.error(f"Error in cost forecasting: {e}")
            return await self._generate_fallback_cost_forecast(sku, historical_data, forecast_days)
    
    async def _generate_fallback_forecast(self, sku: str, historical_data: List[Dict], forecast_days: int) -> Dict[str, Any]:
        """Generate fallback synthetic forecast when Gemma is unavailable"""
        
        # Calculate base demand from historical data
        if historical_data:
            recent_demands = [record.get('demand', 50) for record in historical_data[-7:]]
            base_demand = np.mean(recent_demands) if recent_demands else 50
        else:
            base_demand = 50
        
        # Generate forecast with some variation
        forecast = []
        total_demand = 0
        
        for day in range(1, forecast_days + 1):
            # Add some seasonality and randomness
            seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * day / 7)  # Weekly pattern
            trend_factor = 1 + 0.02 * (day / forecast_days)  # Slight upward trend
            random_factor = 1 + np.random.normal(0, 0.1)  # Random variation
            
            predicted = int(base_demand * seasonal_factor * trend_factor * random_factor)
            forecast.append({"day": day, "predicted_demand": max(1, predicted)})
            total_demand += predicted
        
        return {
            "forecast": forecast,
            "total_predicted_demand": int(total_demand),
            "confidence_level": 65,
            "insights": ["Synthetic forecast - Gemma model unavailable", "Stable demand pattern expected"],
            "model": "fallback"
        }
    
    async def _generate_fallback_cost_forecast(self, sku: str, historical_data: List[Dict], forecast_days: int) -> Dict[str, Any]:
        """Generate fallback synthetic cost forecast"""
        
        # Calculate base cost from historical data
        if historical_data:
            recent_costs = [record.get('cost', 25.0) for record in historical_data[-7:]]
            base_cost = np.mean(recent_costs) if recent_costs else 25.0
        else:
            base_cost = 25.0
        
        # Generate cost forecast
        forecast = []
        total_cost = 0
        
        for day in range(1, forecast_days + 1):
            # Add slight inflation and randomness
            inflation_factor = 1 + 0.001 * day  # Small daily inflation
            random_factor = 1 + np.random.normal(0, 0.05)  # Random variation
            
            predicted_cost = round(base_cost * inflation_factor * random_factor, 2)
            forecast.append({"day": day, "predicted_cost": predicted_cost})
            total_cost += predicted_cost
        
        return {
            "forecast": forecast,
            "total_predicted_cost": round(total_cost, 2),
            "trend": "slightly_increasing",
            "recommendations": ["Monitor for cost optimization opportunities", "Consider bulk purchasing"],
            "model": "fallback"
        }


# Global service instances
paraphrase_service = ParaphraseService()
gemma_service = GemmaForecastingService()


async def initialize_ml_services():
    """Initialize all ML services"""
    logger.info("Initializing ML services...")
    await paraphrase_service.initialize()
    await gemma_service.initialize()
    logger.info("ML services initialized successfully")


# Utility functions for data processing
def detect_file_encoding(file_content: bytes) -> str:
    """Detect file encoding"""
    try:
        import chardet
        result = chardet.detect(file_content)
        return result['encoding'] or 'utf-8'
    except Exception:
        return 'utf-8'


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
