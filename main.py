from fastapi import FastAPI
from routes import demand, inventory, logistics

app = FastAPI(title="AI Supply Chain Backend")

# Register API routers
app.include_router(demand.router, prefix="/demand", tags=["Demand Forecasting"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory Management"])
app.include_router(logistics.router, prefix="/logistics", tags=["Logistics Optimization"])

@app.get("/")
def root():
    return {"message": "AI-Powered Supply Chain Backend is running 🚀"}
