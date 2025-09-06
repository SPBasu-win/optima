"""
Test script for CSV ML functionality

This script tests the complete CSV ML workflow:
1. Upload and analyze CSV files
2. Generate demand forecasts
3. Perform inventory optimization
4. Validate results
"""

import requests
import json
import os
import sys
from typing import Dict, Any

# API Base URL
BASE_URL = "http://localhost:8000/api/v1/csv-ml"

def test_csv_analysis(file_path: str, description: str) -> Dict[str, Any]:
    """Test CSV file analysis"""
    print(f"\n{'='*60}")
    print(f"Testing CSV Analysis: {description}")
    print(f"File: {file_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return {"success": False, "error": "File not found"}
    
    try:
        # Upload and analyze CSV
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file, 'text/csv')}
            response = requests.post(f"{BASE_URL}/analyze", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ CSV Analysis Successful!")
            print(f"📊 Data Shape: {result['data_analysis']['total_rows']} rows, {result['data_analysis']['total_columns']} columns")
            print(f"📈 Data Quality Score: {result['data_analysis']['data_quality_score']:.1f}%")
            print(f"🤖 Recommended ML Tasks: {', '.join(result['recommended_ml_tasks'])}")
            print(f"📋 Columns: {', '.join(result['columns'][:5])}{'...' if len(result['columns']) > 5 else ''}")
            
            # Extract session_id from response
            session_id = result.get('session_id')
            if session_id:
                result['session_id'] = session_id
                print(f"🔑 Session ID: {session_id}")
            
            return result
        else:
            print(f"❌ Analysis failed: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return {"success": False, "error": str(e)}

def test_demand_forecasting(session_id: str, date_col: str, demand_col: str, product_col: str = None) -> Dict[str, Any]:
    """Test demand forecasting"""
    print(f"\n{'='*60}")
    print("Testing Demand Forecasting")
    print(f"{'='*60}")
    
    try:
        # Prepare forecast request
        forecast_data = {
            "date_column": date_col,
            "demand_column": demand_col,
            "forecast_days": 14
        }
        
        if product_col:
            forecast_data["product_column"] = product_col
        
        response = requests.post(
            f"{BASE_URL}/forecast/{session_id}",
            json=forecast_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Demand Forecasting Successful!")
            print(f"📊 Data Points Used: {result['data_points_used']}")
            print(f"📅 Forecast Horizon: {result['forecast_horizon_days']} days")
            
            # Show forecast results
            forecast_results = result['forecast_results']
            if isinstance(forecast_results, dict):
                for product, forecast in forecast_results.items():
                    if isinstance(forecast, dict) and 'summary' in forecast:
                        summary = forecast['summary']
                        print(f"📈 {product}: {summary['total_predicted_demand']} total demand, {summary['average_daily_demand']} avg daily")
            
            return result
        else:
            print(f"❌ Forecasting failed: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"❌ Error during forecasting: {e}")
        return {"success": False, "error": str(e)}

def test_inventory_optimization(session_id: str, product_col: str, stock_col: str, sales_col: str = None, cost_col: str = None) -> Dict[str, Any]:
    """Test inventory optimization"""
    print(f"\n{'='*60}")
    print("Testing Inventory Optimization")
    print(f"{'='*60}")
    
    try:
        # Prepare optimization request
        optimization_data = {
            "product_column": product_col,
            "stock_column": stock_col
        }
        
        if sales_col:
            optimization_data["sales_column"] = sales_col
        if cost_col:
            optimization_data["cost_column"] = cost_col
        
        response = requests.post(
            f"{BASE_URL}/optimize/{session_id}",
            json=optimization_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Inventory Optimization Successful!")
            
            # Show inventory analysis
            inventory_analysis = result['inventory_analysis']
            print(f"📊 Total Products: {inventory_analysis['total_products']}")
            print(f"📦 Average Stock Level: {inventory_analysis['average_stock_level']:.1f}")
            
            # Show stock distribution
            stock_dist = inventory_analysis['stock_distribution']
            print(f"📈 Stock Distribution: Low({stock_dist['low_stock']}), Medium({stock_dist['medium_stock']}), High({stock_dist['high_stock']})")
            
            # Show recommendations summary
            stock_recs = result['stock_recommendations']['summary']
            print(f"🎯 Recommendations: {stock_recs['products_to_reorder']} to reorder, {stock_recs['critical_items']} critical items")
            
            # Show ABC analysis
            abc_analysis = result['abc_analysis']
            if 'summary' in abc_analysis:
                abc_summary = abc_analysis['summary']
                print(f"🔤 ABC Analysis: A({abc_summary['A_products']['count']}), B({abc_summary['B_products']['count']}), C({abc_summary['C_products']['count']})")
            
            return result
        else:
            print(f"❌ Optimization failed: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        return {"success": False, "error": str(e)}

def test_quick_insights(session_id: str) -> Dict[str, Any]:
    """Test quick insights"""
    print(f"\n{'='*60}")
    print("Testing Quick Insights")
    print(f"{'='*60}")
    
    try:
        response = requests.post(f"{BASE_URL}/quick-insights/{session_id}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Quick Insights Generated!")
            
            # Show data overview
            overview = result['data_overview']
            print(f"📊 Data Overview: {overview['total_rows']} rows, {overview['total_columns']} columns")
            print(f"💾 Memory Usage: {overview['memory_usage_mb']} MB")
            
            # Show data quality
            quality = result['data_quality']
            print(f"✅ Data Quality: {quality['complete_rows']} complete rows, {quality['missing_data_percentage']:.1f}% missing")
            
            # Show insights
            if result['key_insights']:
                print("💡 Key Insights:")
                for insight in result['key_insights']:
                    print(f"   • {insight}")
            
            # Show recommendations
            if result['recommended_actions']:
                print("🎯 Recommended Actions:")
                for action in result['recommended_actions']:
                    print(f"   • {action}")
            
            return result
        else:
            print(f"❌ Insights failed: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"❌ Error generating insights: {e}")
        return {"success": False, "error": str(e)}

def main():
    """Run all CSV ML tests"""
    print("🚀 Starting CSV ML Testing Suite")
    print("Make sure the backend server is running at http://localhost:8000")
    
    # Test 1: Sales Data Analysis and Forecasting
    print("\n" + "="*80)
    print("TEST 1: SALES DATA ANALYSIS AND FORECASTING")
    print("="*80)
    
    sales_file = "sample_data/sales_data.csv"
    sales_analysis = test_csv_analysis(sales_file, "Sales Data for Demand Forecasting")
    
    if sales_analysis.get("success"):
        session_id = sales_analysis.get("session_id")
        if session_id:
            # Test forecasting
            test_demand_forecasting(session_id, "date", "sales", "product")
            
            # Test quick insights
            test_quick_insights(session_id)
    
    # Test 2: Inventory Data Analysis and Optimization
    print("\n" + "="*80)
    print("TEST 2: INVENTORY DATA ANALYSIS AND OPTIMIZATION")
    print("="*80)
    
    inventory_file = "sample_data/inventory_data.csv"
    inventory_analysis = test_csv_analysis(inventory_file, "Inventory Data for Optimization")
    
    if inventory_analysis.get("success"):
        session_id = inventory_analysis.get("session_id")
        if session_id:
            # Test inventory optimization
            test_inventory_optimization(session_id, "product_name", "current_stock", "sales_last_month", "unit_price")
            
            # Test quick insights
            test_quick_insights(session_id)
    
    print("\n" + "="*80)
    print("🎉 CSV ML Testing Complete!")
    print("="*80)
    print("\n📖 Usage Instructions:")
    print("1. Upload CSV files using POST /api/v1/csv-ml/analyze")
    print("2. Use the returned session_id for subsequent operations")
    print("3. Generate forecasts with POST /api/v1/csv-ml/forecast/{session_id}")
    print("4. Optimize inventory with POST /api/v1/csv-ml/optimize/{session_id}")
    print("5. Get insights with POST /api/v1/csv-ml/quick-insights/{session_id}")
    print("\n🔍 API Documentation: http://localhost:8000/docs#/csv-ml")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
