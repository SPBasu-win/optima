# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

AI Supply Chain Backend is a FastAPI-based service for AI-powered supply chain management that addresses three major problems:
- Messy and duplicated inventory data
- Manual updates that waste time  
- Lack of real-time visibility across supply chains

The platform provides a Supply Chain Command Center with data organization, demand prediction, invoice digitization, and delivery optimization.

## Common Development Commands

### Environment Setup
```bash path=null start=null
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash path=null start=null
# Method 1: Using the run script (recommended for development)
python run.py

# Method 2: Direct uvicorn command
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Method 3: Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Development and Testing
```bash path=null start=null
# Install development dependencies (if pytest is added)
pip install pytest pytest-asyncio httpx

# Run tests (when test suite is implemented)
pytest tests/ -v

# Check code formatting with black (if added)
black routes/ services/ models/ main.py

# Lint with flake8 (if added)
flake8 routes/ services/ models/ main.py
```

### API Documentation
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- API base URL: http://localhost:8000

## Architecture Overview

### Core Structure
The application follows a layered FastAPI architecture:

```
routes/          # API endpoints organized by domain
├── demand.py    # Demand forecasting endpoints
├── inventory.py # Inventory management endpoints  
└── logistics.py # Logistics optimization endpoints

services/        # Business logic and ML models
└── demand_forecasting.py  # Prophet-based forecasting

models/          # Data models and schemas (Pydantic)
```

### Key Components

**Main Application (`main.py`)**:
- FastAPI app initialization with title "AI Supply Chain Backend"
- Router registration with domain-specific prefixes (/demand, /inventory, /logistics)
- Root endpoint returns startup confirmation

**Route Architecture**:
- Each route module exports a FastAPI `APIRouter` instance
- Consistent error handling with status/message response format
- Pydantic models for request/response validation

**Services Layer**:
- `demand_forecasting.py`: Uses Facebook Prophet for 7-day demand forecasting
- Takes historical sales data as input, returns forecasted values with dates
- Business logic separated from API routing concerns

### Technology Stack

**Current Implementation**:
- **FastAPI 0.104.1**: High-performance API framework
- **Prophet 1.1.4**: Time series forecasting by Meta
- **Pandas 2.1.3**: Data manipulation and analysis
- **Uvicorn 0.24.0**: ASGI server with hot reload

**Planned Integrations** (from project vision):
- **Next.js + React**: Dashboard UI for inventory and insights
- **MongoDB + Cloud Storage**: Persistent data storage
- **OCR + YOLO**: Invoice digitization and item detection
- **OR-Tools**: Advanced logistics optimization
- **APIs**: Integration with existing warehouse/invoice systems

### API Endpoints

**Demand Forecasting** (`/demand/`):
- `POST /forecast`: Generate 7-day demand forecast from historical sales data

**Inventory Management** (`/inventory/`):
- `GET /status`: Retrieve current inventory status
- `POST /optimize`: Get inventory optimization recommendations based on stock levels

**Logistics Optimization** (`/logistics/`):
- `POST /optimize-routes`: Optimize delivery routes for multiple destinations
- `POST /calculate-shipping`: Calculate shipping costs based on weight and urgency

### Development Patterns

**Request/Response Structure**:
All endpoints follow consistent response format:
```json
{
  "status": "success|error",
  "message": "descriptive message",
  "data|forecast|recommendations": {}
}
```

**Error Handling**:
Routes use try-catch blocks returning structured error responses rather than raising HTTP exceptions.

**Model Validation**:
Pydantic models define request schemas with type hints and validation (e.g., `list[int]` for Python 3.9+ syntax).

### Hot Reload Configuration
The `run.py` script configures uvicorn with reload monitoring for:
- `routes/` directory
- `services/` directory  
- `models/` directory

This enables automatic server restart when files in these directories change during development.

## Development Notes

- This is a hackathon project designed for rapid iteration and extension
- The modular structure allows easy addition of new domains (routes + services)
- Prophet forecasting requires sufficient historical data points for meaningful predictions
- Current logistics optimization uses placeholder algorithms - integrate OR-Tools for production use
- Consider adding database integration (MongoDB) for persistent storage beyond the current in-memory approach
