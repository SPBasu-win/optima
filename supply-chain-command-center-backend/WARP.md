# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Supply Chain Command Center Backend** built with FastAPI, providing comprehensive supply chain management capabilities including inventory management, invoice digitization with OCR, demand forecasting using ML, and logistics optimization.

### Key Technologies
- **FastAPI 0.104+**: Modern async Python web framework
- **MongoDB 7.0**: Document database with Motor async driver  
- **Redis**: Caching and session management
- **Prophet**: Time series forecasting for demand prediction
- **OR-Tools**: Constraint optimization for logistics
- **Tesseract OCR**: Invoice digitization and processing
- **OpenCV**: Image preprocessing for OCR
- **Docker**: Containerized deployment

## Common Commands

### Development Setup

```bash
# Quick start with Docker (recommended)
docker-compose up -d

# Manual setup with virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Quick API test (works without database)
python test_api.py

# Run full test suite
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_inventory.py -v
```

### Database Operations

```bash
# Create database indexes (one-time setup)
python -c "
from app.core.database import db_manager
import asyncio
asyncio.run(db_manager.create_indexes())
"

# Access MongoDB admin interface
# http://localhost:8081 (when running with docker-compose)
```

### Development Tools

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Run Celery worker for background tasks
celery -A app.core.celery worker --loglevel=info

# Monitor Celery tasks with Flower
celery -A app.core.celery flower --port=5555
```

### Docker Operations

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale API instances
docker-compose up -d --scale api=3

# Run with background workers
docker-compose --profile worker up -d

# Production deployment
docker-compose --profile production up -d

# Stop all services
docker-compose down

# Rebuild containers
docker-compose up -d --build
```

## Architecture Overview

### Application Structure
```
app/
├── api/v1/endpoints/     # REST API endpoints by domain
├── core/                # Configuration and database setup  
├── models/              # Pydantic data models
└── services/            # Business logic services
```

### Key Architectural Patterns

**Service Layer Architecture**: Business logic is encapsulated in service classes (`inventory_service.py`, `forecasting_service.py`, `logistics_service.py`, etc.) that are called by API endpoints.

**Async Database Operations**: Uses Motor for async MongoDB operations with proper connection lifecycle management in `main.py`.

**Domain-Driven Design**: Code is organized by business domains (inventory, invoices, forecasting, logistics) with dedicated models and services for each.

**ML Pipeline Integration**: Forecasting service uses Prophet models with caching and background training. Models are stored in the `models/` directory and loaded on demand.

**OCR Processing Pipeline**: Multi-stage pipeline for invoice processing: file upload → image preprocessing → OCR extraction → data validation → storage.

### Core Services

- **InventoryService**: CRUD operations, stock movements, deduplication, low stock alerts
- **ForecastingService**: Prophet-based demand forecasting with model caching and batch processing
- **LogisticsService**: OR-Tools based route optimization for delivery planning  
- **OCRService**: Tesseract-based invoice digitization with image preprocessing
- **DashboardService**: Aggregates KPIs, alerts, and analytics from all domains

### Database Design

**Collections**: 
- `inventory_items`: Product catalog with stock levels
- `stock_movements`: Audit trail of all inventory changes
- `invoices`: Processed invoices with OCR extracted data
- `suppliers`, `warehouses`: Master data entities
- `demand_forecasts`: Cached ML predictions

**Key Patterns**:
- Uses MongoDB's document model for flexible schemas
- Implements proper indexing for query performance
- Async operations throughout with Motor driver
- Aggregation pipelines for analytics and reporting

### Configuration Management

Environment-based configuration using Pydantic Settings in `app/core/config.py`. Key settings include:
- Database URLs (MongoDB, Redis)
- File upload paths and limits
- ML model directories
- OCR executable paths
- Security keys and tokens

### API Design Principles

- RESTful endpoint design with consistent patterns
- Comprehensive Pydantic models for request/response validation
- Async endpoint handlers for non-blocking I/O
- Structured error handling with meaningful HTTP status codes
- OpenAPI/Swagger documentation auto-generated at `/docs`

## Key Endpoints

### Core Business Operations
- `GET/POST /api/v1/inventory/` - Inventory CRUD operations
- `POST /api/v1/inventory/{sku}/stock-movement` - Record stock changes  
- `POST /api/v1/invoices/upload` - OCR invoice processing
- `GET /api/v1/forecasting/demand/{sku}` - ML demand forecasting
- `POST /api/v1/logistics/optimize-routes` - Route optimization

### Analytics & Dashboard  
- `GET /api/v1/dashboard/summary` - Complete dashboard data
- `GET /api/v1/inventory/low-stock/items` - Stock alerts
- `GET /api/v1/dashboard/kpis` - Key performance indicators

### Batch Operations
- `POST /api/v1/forecasting/generate` - Batch forecast generation
- `POST /api/v1/inventory/deduplicate` - Find/remove duplicates

## Development Guidelines

### Adding New Features
1. Create Pydantic models in `app/models/`
2. Implement business logic in `app/services/`  
3. Add API endpoints in `app/api/v1/endpoints/`
4. Register routes in `app/api/v1/api.py`
5. Write tests covering the new functionality

### Working with ML Models
- Prophet models are cached in memory and persisted to disk
- Use ThreadPoolExecutor for CPU-intensive ML operations to avoid blocking
- Forecasting service handles model lifecycle (training, caching, updates)
- OR-Tools operations should be wrapped in async executors

### OCR Processing Guidelines
- Supported formats: PDF, JPG, PNG
- Images are preprocessed with OpenCV for better OCR accuracy
- OCR extraction includes confidence scoring and validation
- Process large files asynchronously to avoid timeouts

### Performance Considerations
- Database queries use proper indexes and aggregation pipelines
- Redis caching for frequently accessed data  
- Connection pooling for database operations
- Background task processing with Celery for heavy operations
- Async/await throughout for non-blocking I/O

### Testing Strategy
- Use `test_api.py` for quick smoke tests without database
- Full pytest suite requires running MongoDB and Redis
- Test database operations use separate test collections
- Mock external services (OCR, ML models) in unit tests

<citations>
<document>
<document_type>RULE</document_type>
<document_id>15JHEnLUUysWuYUo4ni9JF</document_id>
</document>
</citations>
