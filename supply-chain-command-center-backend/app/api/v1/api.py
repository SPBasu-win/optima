from fastapi import APIRouter
from app.api.v1.endpoints import inventory, invoices, forecasting, logistics, dashboard, suppliers, warehouses, data_import, csv_ml

api_router = APIRouter()

api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["warehouses"])
api_router.include_router(forecasting.router, prefix="/forecasting", tags=["forecasting"])
api_router.include_router(logistics.router, prefix="/logistics", tags=["logistics"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(data_import.router, prefix="/data-import", tags=["data-import"])
api_router.include_router(csv_ml.router, prefix="/csv-ml", tags=["csv-ml"])
