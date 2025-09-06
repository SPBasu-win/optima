# 🤖 CSV ML Integration Guide

## Overview

The Optima AI Supply Chain Platform now includes comprehensive **Machine Learning functionality** that works directly with **CSV files**. This powerful integration allows you to:

- 📊 **Analyze CSV data** with automatic pattern detection
- 📈 **Generate demand forecasts** using Prophet and advanced ML models
- 🎯 **Optimize inventory levels** with ML-driven recommendations
- 📋 **Perform ABC analysis** for product classification
- 💡 **Get intelligent insights** and actionable recommendations

---

## 🚀 Quick Start

### 1. Upload and Analyze CSV File
```bash
curl -X POST "http://localhost:8000/api/v1/csv-ml/analyze" \
  -F "file=@your_data.csv"
```

### 2. Generate Demand Forecast
```bash
curl -X POST "http://localhost:8000/api/v1/csv-ml/forecast/{session_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "date_column": "date",
    "demand_column": "sales",
    "product_column": "product",
    "forecast_days": 30
  }'
```

### 3. Optimize Inventory
```bash
curl -X POST "http://localhost:8000/api/v1/csv-ml/optimize/{session_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "product_column": "product_name",
    "stock_column": "current_stock",
    "sales_column": "sales_last_month",
    "cost_column": "unit_price"
  }'
```

---

## 📋 API Endpoints

### File Upload & Analysis

#### `POST /api/v1/csv-ml/analyze`
**Upload and analyze CSV file for ML capabilities**

**Request:**
- **File**: CSV file (multipart/form-data)

**Response:**
```json
{
  "success": true,
  "filename": "sales_data.csv",
  "data_analysis": {
    "total_rows": 1000,
    "total_columns": 5,
    "data_quality_score": 95.2,
    "recommended_ml_tasks": [
      "demand_forecasting",
      "sales_forecasting",
      "inventory_optimization"
    ]
  },
  "columns": ["date", "product", "sales", "price", "cost"],
  "preview": [/* First 10 rows */],
  "session_id": "uuid-string"
}
```

### Demand Forecasting

#### `POST /api/v1/csv-ml/forecast/{session_id}`
**Generate demand forecast from CSV data**

**Request Body:**
```json
{
  "date_column": "date",
  "demand_column": "sales", 
  "product_column": "product",  // optional
  "forecast_days": 30
}
```

**Response:**
```json
{
  "success": true,
  "forecast_results": {
    "Laptop A": {
      "predictions": [
        {
          "date": "2024-01-01",
          "predicted_demand": 15.2,
          "lower_bound": 12.1,
          "upper_bound": 18.9,
          "trend": 0.5
        }
      ],
      "summary": {
        "total_predicted_demand": 456.0,
        "average_daily_demand": 15.2,
        "forecast_period_days": 30
      },
      "model_performance": {
        "mae": 2.1,
        "rmse": 3.4,
        "data_points": 90
      }
    }
  },
  "data_points_used": 90,
  "forecast_horizon_days": 30
}
```

### Inventory Optimization

#### `POST /api/v1/csv-ml/optimize/{session_id}`
**Optimize inventory based on CSV data**

**Request Body:**
```json
{
  "product_column": "product_name",
  "stock_column": "current_stock",
  "sales_column": "sales_last_month",  // optional
  "cost_column": "unit_price"          // optional
}
```

**Response:**
```json
{
  "success": true,
  "inventory_analysis": {
    "total_products": 25,
    "average_stock_level": 45.2,
    "stock_distribution": {
      "low_stock": 5,
      "medium_stock": 15,
      "high_stock": 5
    }
  },
  "optimization_results": {
    "overall_recommendations": [
      "Consider reducing overall stock levels",
      "Review demand patterns for high-stock items"
    ],
    "product_recommendations": [
      {
        "product": "Laptop Dell Inspiron",
        "recommendations": ["Increase stock level - understocked"],
        "priority": "high"
      }
    ]
  },
  "abc_analysis": {
    "classification": {
      "Laptop Dell Inspiron": "A",
      "Wireless Mouse": "B",
      "USB Cable": "C"
    },
    "summary": {
      "A_products": {"count": 5, "products": ["Laptop Dell Inspiron"]},
      "B_products": {"count": 8, "products": ["Wireless Mouse"]},
      "C_products": {"count": 12, "products": ["USB Cable"]}
    },
    "recommendations": {
      "A_products": "High priority - tight control, frequent monitoring",
      "B_products": "Medium priority - periodic review",
      "C_products": "Low priority - simple controls"
    }
  },
  "stock_recommendations": {
    "reorder_recommendations": [
      {
        "product": "Conference Phone",
        "current_stock": 5,
        "recommended_reorder_point": 15,
        "suggested_order_quantity": 25,
        "urgency": "high"
      }
    ],
    "excess_stock_alerts": [
      {
        "product": "USB Cable Type-C",
        "current_stock": 200,
        "recommended_stock_level": 75,
        "excess_quantity": 125
      }
    ],
    "critical_items": [
      {
        "product": "Conference Phone", 
        "current_stock": 5,
        "risk_level": "critical",
        "immediate_action_required": true
      }
    ]
  }
}
```

### Quick Insights

#### `POST /api/v1/csv-ml/quick-insights/{session_id}`
**Get rapid ML insights from CSV data**

**Response:**
```json
{
  "data_overview": {
    "total_rows": 1000,
    "total_columns": 5,
    "memory_usage_mb": 0.8,
    "data_types": {"object": 2, "float64": 2, "datetime64": 1}
  },
  "data_quality": {
    "complete_rows": 950,
    "missing_data_percentage": 5.0,
    "columns_with_missing_data": ["supplier"]
  },
  "key_insights": [
    "Dataset contains 3 numeric columns suitable for ML analysis",
    "Time series analysis possible with columns: date",
    "Inventory data detected in columns: current_stock"
  ],
  "recommended_actions": [
    "Consider demand forecasting with time series data",
    "Run inventory optimization analysis"
  ]
}
```

### Session Management

#### `GET /api/v1/csv-ml/sessions`
**List all active CSV ML sessions**

#### `GET /api/v1/csv-ml/session/{session_id}/info` 
**Get detailed information about a specific session**

#### `DELETE /api/v1/csv-ml/session/{session_id}`
**Delete a CSV ML session**

---

## 📊 Supported CSV Formats

### Sales/Demand Data Format
For demand forecasting, your CSV should include:

```csv
date,product,sales,price,cost
2023-01-01,Laptop A,10,999.99,650.00
2023-01-02,Laptop A,8,999.99,650.00
2023-01-03,Mouse B,45,29.99,12.00
```

**Required columns:**
- **Date column**: Any date format (auto-detected)
- **Demand/Sales column**: Numeric values representing demand or sales

**Optional columns:**
- **Product column**: For multi-product forecasting
- **Price/Cost columns**: For revenue analysis

### Inventory Data Format
For inventory optimization, your CSV should include:

```csv
product_name,current_stock,unit_price,sales_last_month,supplier,category
Laptop Dell Inspiron,25,899.99,45,Dell Inc,Electronics
Wireless Mouse,150,24.99,120,Logitech,Accessories
```

**Required columns:**
- **Product column**: Product names/IDs
- **Stock column**: Current inventory levels

**Optional columns:**
- **Sales column**: Historical sales data
- **Cost/Price column**: For value analysis
- **Category/Supplier columns**: For segmentation

---

## 🤖 Machine Learning Models

### Demand Forecasting Models

1. **Prophet (Primary)**
   - Facebook's time series forecasting tool
   - Handles seasonality, trends, and holidays
   - Provides confidence intervals
   - Best for: Regular time series data

2. **Simple Trend (Fallback)**
   - Linear regression-based forecasting
   - Fast and reliable fallback
   - Best for: Limited data or Prophet failures

### Inventory Optimization Models

1. **ABC Analysis**
   - Categorizes products by importance (A, B, C)
   - Based on sales volume × cost
   - Helps prioritize inventory management

2. **Stock Level Optimization**
   - Identifies overstocked and understocked items
   - Calculates optimal reorder points
   - Provides safety stock recommendations

3. **Statistical Analysis**
   - Outlier detection using IQR method
   - Correlation analysis between variables
   - Trend analysis for inventory patterns

---

## 📈 Key Features

### ✅ **Automatic Data Processing**
- **Smart column detection**: Automatically identifies date, numeric, and categorical columns
- **Data cleaning**: Handles missing values and inconsistent formats
- **Column standardization**: Maps various column names to standard formats

### ✅ **Advanced Analytics**
- **Pattern detection**: Identifies seasonality, trends, and correlations
- **Data quality scoring**: Evaluates data completeness and reliability
- **Outlier detection**: Finds anomalous data points

### ✅ **Intelligent Recommendations**
- **ML task suggestions**: Recommends suitable analyses based on data structure
- **Actionable insights**: Provides specific recommendations for inventory management
- **Priority classification**: Highlights critical items requiring immediate attention

### ✅ **Performance Optimization**
- **Async processing**: Non-blocking ML operations
- **Session management**: Efficient data storage and retrieval
- **Batch operations**: Process multiple products simultaneously
- **Fallback mechanisms**: Ensures reliable results even with limited data

---

## 🧪 Testing

### Run the Test Suite
```bash
cd supply-chain-command-center-backend
python test_csv_ml.py
```

The test suite includes:
- ✅ CSV file upload and analysis
- ✅ Demand forecasting with sample sales data  
- ✅ Inventory optimization with sample inventory data
- ✅ Quick insights generation
- ✅ Session management operations

### Sample Data Files
- **`sample_data/sales_data.csv`**: Time series sales data for forecasting
- **`sample_data/inventory_data.csv`**: Inventory data for optimization

---

## 💡 Best Practices

### Data Preparation
1. **Clean your data**: Remove or handle missing values appropriately
2. **Consistent formats**: Use standard date formats (YYYY-MM-DD recommended)
3. **Meaningful column names**: Use descriptive names for better auto-detection
4. **Sufficient data**: Minimum 10 data points for forecasting, 20+ recommended

### Usage Patterns
1. **Start with analysis**: Always begin with `/analyze` to understand your data
2. **Review recommendations**: Check the `recommended_ml_tasks` before proceeding
3. **Validate results**: Review model performance metrics and confidence intervals
4. **Iterate and improve**: Use insights to refine your data and processes

### Performance Tips
1. **Limit data size**: For large files (>10MB), consider sampling or preprocessing
2. **Use appropriate forecast horizons**: Longer forecasts require more historical data
3. **Cache sessions**: Reuse session IDs to avoid re-uploading data
4. **Monitor resources**: ML operations are CPU-intensive

---

## 🔧 Configuration

### Environment Variables
```env
# ML Service Configuration
MODEL_DIR=./models                    # Directory for storing trained models
MAX_FORECAST_DAYS=365                # Maximum forecast horizon
MAX_PRODUCTS_BATCH=10               # Maximum products for batch processing
CSV_MAX_ROWS=10000                  # Maximum rows per CSV file

# Prophet Configuration  
PROPHET_CHANGEPOINT_PRIOR=0.05      # Trend flexibility
PROPHET_SEASONALITY_PRIOR=10.0      # Seasonality strength
PROPHET_UNCERTAINTY_SAMPLES=1000    # Confidence interval samples
```

### Model Caching
- Trained models are cached in `./models/` directory
- Models are reused if trained within the last 7 days
- Automatic cleanup of old model files

---

## 🚨 Troubleshooting

### Common Issues

#### **"Insufficient historical data"**
- **Solution**: Provide at least 10 data points for forecasting
- **Tip**: Aggregate daily data if you have hourly/minute-level data

#### **"Column not found in data"**
- **Solution**: Check exact column names in your CSV
- **Tip**: Use `/session/{id}/info` to see detected columns

#### **"Prophet forecasting error"**
- **Solution**: System automatically falls back to simple trend forecasting
- **Tip**: Ensure date column is properly formatted

#### **"Session not found"**
- **Solution**: Re-upload your CSV file to get a new session ID
- **Tip**: Sessions are cleared on server restart

#### **Poor forecast accuracy**
- **Solution**: Provide more historical data and ensure data quality
- **Tip**: Check for outliers and missing values

### Performance Issues

#### **Slow processing**
- **Solution**: Reduce data size or increase server resources
- **Tip**: Use sampling for exploration, full data for production

#### **Memory errors**
- **Solution**: Process smaller batches or increase available RAM
- **Tip**: Consider data preprocessing before upload

---

## 🔗 Integration Examples

### Python Integration
```python
import requests
import pandas as pd

# Upload CSV
with open('sales_data.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/csv-ml/analyze',
        files={'file': f}
    )
    
session_id = response.json()['session_id']

# Generate forecast
forecast_response = requests.post(
    f'http://localhost:8000/api/v1/csv-ml/forecast/{session_id}',
    json={
        'date_column': 'date',
        'demand_column': 'sales', 
        'forecast_days': 30
    }
)

forecast_data = forecast_response.json()
```

### JavaScript Integration
```javascript
// Upload CSV
const formData = new FormData();
formData.append('file', csvFile);

const uploadResponse = await fetch('/api/v1/csv-ml/analyze', {
    method: 'POST',
    body: formData
});

const { session_id } = await uploadResponse.json();

// Generate forecast
const forecastResponse = await fetch(`/api/v1/csv-ml/forecast/${session_id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        date_column: 'date',
        demand_column: 'sales',
        forecast_days: 30
    })
});

const forecastData = await forecastResponse.json();
```

---

## 📚 Resources

- **API Documentation**: http://localhost:8000/docs#/csv-ml
- **Prophet Documentation**: https://facebook.github.io/prophet/
- **Scikit-learn Guide**: https://scikit-learn.org/stable/user_guide.html
- **Test Suite**: `test_csv_ml.py`
- **Sample Data**: `sample_data/`

---

**🎉 Ready to harness the power of ML with your CSV data!**

*For additional support or feature requests, check the main project documentation or submit an issue on GitHub.*
