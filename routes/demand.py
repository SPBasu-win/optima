from fastapi import APIRouter
from pydantic import BaseModel
from services.demand_forecasting import forecast_demand

router = APIRouter()

class SalesData(BaseModel):
    past_sales: list[int]

@router.post("/forecast")
def get_demand_forecast(sales_data: SalesData):
    """
    Forecast demand for the next 7 days based on historical sales data
    """
    try:
        forecast = forecast_demand(sales_data.past_sales)
        return {
            "status": "success",
            "forecast": forecast,
            "message": "Demand forecast generated successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate forecast: {str(e)}"
        }
