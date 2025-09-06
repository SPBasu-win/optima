from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import db_manager
from app.api.v1.api import api_router
from app.services.ml_services_simple import initialize_ml_services

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_manager.connect_to_mongo()
    await db_manager.create_indexes()
    # Initialize ML services (paraphrase and Gemma models)
    await initialize_ml_services()
    yield
    # Shutdown
    await db_manager.close_mongo_connection()

app = FastAPI(
    title="Supply Chain Command Center API",
    description="A comprehensive platform for supply chain management with data collection, cleaning, predictions, and digitization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "Supply Chain Command Center API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
