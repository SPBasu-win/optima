# Supply Chain Command Center - Backend API

A comprehensive supply chain management platform that provides real-time visibility, intelligent automation, and optimized decision-making for modern businesses.

## 🚀 Overview

The Supply Chain Command Center addresses three major challenges in today's supply chains:
- **Messy Data**: Automatically cleans and organizes inventory data, removing duplicates
- **Manual Updates**: Automates data processing with OCR for invoice digitization
- **Limited Visibility**: Provides real-time dashboards and predictive analytics

## ✨ Features

### Core Functionality
- **🏭 Inventory Management**: Complete CRUD operations with real-time stock tracking
- **📄 Invoice Digitization**: OCR-powered automatic invoice processing and data extraction
- **📊 Demand Forecasting**: ML-powered predictions using Prophet and historical data
- **🚛 Logistics Optimization**: Route optimization using OR-Tools for efficient deliveries
- **📈 Real-time Dashboard**: Comprehensive supply chain visibility and analytics
- **🤖 Data Deduplication**: Intelligent duplicate detection and resolution

### Technical Features
- **FastAPI**: High-performance async REST API
- **MongoDB**: Scalable document-based data storage
- **OCR Processing**: Tesseract-powered document digitization
- **Machine Learning**: Prophet for forecasting, OR-Tools for optimization
- **Docker Support**: Containerized deployment with docker-compose
- **Real-time Processing**: Async operations for better performance

## 🛠️ Technology Stack

- **Backend Framework**: FastAPI 0.104+
- **Database**: MongoDB with Motor (async driver)
- **Cache**: Redis for session management and caching
- **OCR**: Tesseract with OpenCV for image preprocessing
- **Machine Learning**: 
  - Prophet for demand forecasting
  - OR-Tools for logistics optimization
  - Scikit-learn for general ML operations
- **Computer Vision**: YOLO (Ultralytics) for stock item detection
- **Task Queue**: Celery with Redis broker
- **Deployment**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- MongoDB 7.0+
- Redis 7.2+
- Tesseract OCR

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd supply-chain-command-center-backend
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Access the API**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - MongoDB Admin: http://localhost:8081

### Manual Installation

1. **Install system dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils
   
   # macOS
   brew install tesseract poppler
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export MONGODB_URL=mongodb://localhost:27017
   export DATABASE_NAME=supply_chain_db
   export REDIS_URL=redis://localhost:6379
   ```

4. **Start the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📁 Project Structure

```
supply-chain-command-center-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/          # API endpoint modules
│   │       │   ├── inventory.py    # Inventory management
│   │       │   ├── invoices.py     # Invoice processing
│   │       │   ├── suppliers.py    # Supplier management
│   │       │   ├── warehouses.py   # Warehouse operations
│   │       │   ├── forecasting.py  # Demand forecasting
│   │       │   ├── logistics.py    # Route optimization
│   │       │   └── dashboard.py    # Dashboard analytics
│   │       └── api.py              # API router configuration
│   ├── core/
│   │   ├── config.py               # Application configuration
│   │   └── database.py             # Database connection
│   ├── models/
│   │   ├── inventory.py            # Inventory data models
│   │   ├── invoices.py             # Invoice data models
│   │   ├── suppliers.py            # Supplier data models
│   │   └── warehouses.py           # Warehouse data models
│   └── services/
│       ├── inventory_service.py    # Inventory business logic
│       ├── ocr_service.py          # OCR processing
│       ├── forecasting_service.py  # ML forecasting
│       └── logistics_service.py    # Route optimization
├── uploads/                        # File upload directory
├── temp/                           # Temporary processing files
├── models/                         # ML model storage
├── tests/                          # Test files
├── docker-compose.yml              # Docker services
├── Dockerfile                      # Container definition
├── requirements.txt                # Python dependencies
└── main.py                         # Application entry point
```

## 🔧 Configuration

Create a `.env` file in the root directory:

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=supply_chain_db

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
UPLOAD_DIR=uploads
TEMP_DIR=temp
MAX_FILE_SIZE=10485760

# OCR
TESSERACT_CMD=/usr/bin/tesseract

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password

# Environment
ENVIRONMENT=development
```

## 📊 API Documentation

### Core Endpoints

#### Inventory Management
- `GET /api/v1/inventory/` - List inventory items with filtering
- `POST /api/v1/inventory/` - Create new inventory item
- `GET /api/v1/inventory/{sku}` - Get specific item by SKU
- `PUT /api/v1/inventory/{sku}` - Update inventory item
- `DELETE /api/v1/inventory/{sku}` - Delete inventory item
- `POST /api/v1/inventory/{sku}/stock-movement` - Record stock movement
- `GET /api/v1/inventory/low-stock/items` - Get low stock alerts
- `POST /api/v1/inventory/deduplicate` - Find/remove duplicates

#### Invoice Processing
- `POST /api/v1/invoices/upload` - Upload and process invoice
- `GET /api/v1/invoices/` - List invoices with filtering
- `GET /api/v1/invoices/{id}` - Get invoice details
- `PUT /api/v1/invoices/{id}/approve` - Approve processed invoice
- `POST /api/v1/invoices/{id}/reprocess` - Reprocess invoice with OCR

#### Supplier Management
- `GET /api/v1/suppliers/` - List suppliers
- `POST /api/v1/suppliers/` - Create supplier
- `GET /api/v1/suppliers/{id}` - Get supplier details
- `PUT /api/v1/suppliers/{id}` - Update supplier

#### Analytics & Forecasting
- `GET /api/v1/forecasting/demand/{sku}` - Get demand forecast
- `POST /api/v1/forecasting/generate` - Generate forecasts
- `GET /api/v1/dashboard/summary` - Dashboard summary
- `GET /api/v1/logistics/optimize-routes` - Route optimization

### Example Usage

```bash
# Get inventory items with low stock
curl -X GET "http://localhost:8000/api/v1/inventory/?low_stock_only=true"

# Upload and process an invoice
curl -X POST "http://localhost:8000/api/v1/invoices/upload" \
     -F "file=@invoice.pdf" \
     -F "invoice_type=purchase"

# Get demand forecast for a product
curl -X GET "http://localhost:8000/api/v1/forecasting/demand/LAPTOP001?days=30"
```

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_inventory.py -v
```

## 🚀 Deployment

### Production Deployment

1. **Set production environment variables**
2. **Build and run with production profile**
   ```bash
   docker-compose --profile production up -d
   ```

### Scaling

```bash
# Scale API instances
docker-compose up -d --scale api=3

# Start background workers
docker-compose --profile worker up -d
```

### Monitoring

- **API Metrics**: http://localhost:8000/metrics
- **Flower (Celery)**: http://localhost:5555
- **MongoDB Express**: http://localhost:8081

## 🔍 Key Features Deep Dive

### 1. Invoice Digitization with OCR
- Supports PDF, JPG, PNG formats
- Automatic text extraction and validation
- Structured data extraction (amounts, dates, line items)
- Confidence scoring and error handling
- Image preprocessing for better accuracy

### 2. Intelligent Inventory Management
- Real-time stock tracking
- Automatic low stock alerts
- Reorder suggestions based on history
- Duplicate detection and resolution
- Multi-warehouse support

### 3. Demand Forecasting
- Prophet-based time series forecasting
- Seasonal trend analysis
- Multiple forecasting horizons
- Confidence intervals
- Historical accuracy tracking

### 4. Route Optimization
- OR-Tools powered optimization
- Multi-constraint routing
- Real-time traffic consideration
- Delivery time windows
- Vehicle capacity planning

## 🛡️ Security Features

- JWT token authentication
- Rate limiting on API endpoints
- Input validation and sanitization
- File upload restrictions
- HTTPS ready configuration
- Environment-based secrets management

## 🔧 Development

### Adding New Features

1. **Create model in `app/models/`**
2. **Add service logic in `app/services/`**
3. **Create API endpoints in `app/api/v1/endpoints/`**
4. **Register routes in `app/api/v1/api.py`**
5. **Write tests in `tests/`**

### Database Migrations

```bash
# Create indexes
python -c "
from app.core.database import db_manager
import asyncio
asyncio.run(db_manager.create_indexes())
"
```

## 📈 Performance Optimization

- **Async/await**: Non-blocking I/O operations
- **Database Indexing**: Optimized queries
- **Redis Caching**: Frequently accessed data
- **Connection Pooling**: Efficient database connections
- **Image Processing**: Optimized OCR pipeline
- **Background Tasks**: Heavy operations via Celery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `pytest`
5. Commit changes: `git commit -am 'Add feature'`
6. Push to branch: `git push origin feature-name`
7. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint for interactive API docs
- **Issues**: Report bugs and feature requests via GitHub issues
- **Email**: [Your contact email]

## 🚀 Roadmap

- [ ] Advanced ML models for demand forecasting
- [ ] Real-time inventory tracking with IoT integration  
- [ ] Mobile app support
- [ ] Advanced reporting and analytics
- [ ] Multi-tenant support
- [ ] Integration with popular ERP systems
- [ ] Blockchain-based supply chain tracking

---

**Built with ❤️ for modern supply chain management**
