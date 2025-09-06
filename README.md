# 🚀 Optima AI Supply Chain Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.0-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-green?style=flat&logo=mongodb&logoColor=white)](https://mongodb.com)

A comprehensive AI-powered supply chain management platform featuring intelligent data processing, demand forecasting, and automated inventory management.

## 🌟 Features

### 🤖 **AI-Powered Intelligence**
- **Paraphrasing Models**: Automated data cleaning and text normalization using T5 transformers
- **Gemma Forecasting**: Advanced demand and cost predictions using Google's Gemma LLM
- **Smart Data Processing**: Intelligent column mapping and data validation
- **OCR Integration**: Document digitization for invoices and receipts

### 📊 **Advanced Analytics**
- **Real-time Dashboards**: Interactive KPI monitoring and supply chain insights
- **Demand Forecasting**: 7-90 day predictions with confidence intervals
- **Cost Analysis**: Trend analysis and price optimization recommendations
- **Inventory Optimization**: Automated reorder points and stock level alerts

### 📁 **Intelligent Data Management**
- **AI Data Import**: Drag-and-drop CSV/Excel upload with automatic cleaning
- **Column Standardization**: Smart mapping of diverse data formats
- **Duplicate Detection**: Intelligent record deduplication
- **Data Validation**: Real-time error checking and correction suggestions

### 🎨 **Modern User Interface**
- **Dark Theme**: Professional dark mode design with orange accents
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Real-time Updates**: Live data synchronization with React Query
- **Interactive Charts**: Dynamic visualizations for forecasts and trends

## 🏗️ Architecture

```
ai-supply-chain-backend/
├── supply-chain-command-center-backend/    # FastAPI Backend
│   ├── app/
│   │   ├── api/                            # API Routes
│   │   ├── core/                           # Configuration & Database
│   │   ├── models/                         # Pydantic Models
│   │   ├── services/                       # Business Logic
│   │   │   ├── ml_services.py              # AI/ML Services
│   │   │   └── forecasting_service.py      # Forecasting Logic
│   │   └── utils/                          # Utilities
│   ├── main.py                             # Application Entry Point
│   └── requirements.txt                    # Python Dependencies
│
├── supply-chain-frontend/                  # Next.js Frontend
│   ├── src/
│   │   ├── app/                           # App Router Pages
│   │   ├── components/                    # React Components
│   │   ├── lib/                          # Utilities & API Client
│   │   └── types/                        # TypeScript Definitions
│   ├── package.json                      # Node Dependencies
│   └── tailwind.config.js                # Styling Configuration
│
└── docs/                                  # Documentation
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **MongoDB 7.0+**
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-supply-chain-platform.git
cd ai-supply-chain-platform
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd supply-chain-command-center-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB (if local)
mongod --dbpath ./data/db

# Start the backend server
python main.py
```

The backend will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd ../supply-chain-frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at: `http://localhost:3000`

### 4. Environment Configuration

Create `.env` files in both directories:

**Backend (`supply-chain-command-center-backend/.env`):**
```env
MONGODB_URL=mongodb://localhost:27017/supply_chain_db
API_V1_STR=/api/v1
PROJECT_NAME=Supply Chain Command Center
SECRET_KEY=your-secret-key-here
```

**Frontend (`supply-chain-frontend/.env.local`):**
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## 🤖 AI Models Integration

### Paraphrasing Model (T5)
- **Purpose**: Data cleaning and text normalization
- **Model**: `t5-small` from Hugging Face Transformers
- **Usage**: Automatic cleaning of product names, categories, and supplier information

### Gemma LLM Forecasting
- **Purpose**: Demand and cost forecasting
- **Model**: `gemma:2b` via Ollama
- **Features**: Context-aware predictions with business insights

### Setup AI Models

1. **Install Ollama** (for Gemma):
```bash
# Download and install Ollama from https://ollama.com
ollama pull gemma:2b
```

2. **Hugging Face Models** (automatically downloaded on first use):
- T5-small for paraphrasing
- Sentence transformers for embeddings

## 📊 Usage Guide

### 1. Data Import Workflow
1. **Upload**: Drag and drop CSV/Excel files
2. **AI Cleaning**: Automatic text normalization and column mapping
3. **Preview**: Review cleaned data before import
4. **Import**: Bulk insert with duplicate handling

### 2. Demand Forecasting
1. **Select Product**: Choose from inventory SKUs
2. **Set Period**: Configure forecast duration (7-90 days)
3. **Generate**: Get AI-powered predictions with confidence intervals
4. **Analyze**: Review insights and reorder recommendations

### 3. Dashboard Analytics
- **KPI Monitoring**: Real-time inventory metrics
- **Low Stock Alerts**: Automated reorder notifications
- **Trend Analysis**: Historical performance tracking
- **Cost Optimization**: Price trend analysis

## 🛠️ API Endpoints

### Core Endpoints
- `GET /api/v1/inventory/` - List inventory items
- `POST /api/v1/inventory/` - Create inventory item
- `PUT /api/v1/inventory/{sku}` - Update inventory item
- `DELETE /api/v1/inventory/{sku}` - Delete inventory item

### AI-Powered Endpoints
- `POST /api/v1/data-import/upload` - Upload file for processing
- `POST /api/v1/data-import/clean/{upload_id}` - AI data cleaning
- `POST /api/v1/data-import/import` - Import cleaned data
- `GET /api/v1/forecasting/demand/{sku}` - Gemma demand forecast
- `GET /api/v1/forecasting/cost/{sku}` - Gemma cost forecast

### Dashboard Endpoints
- `GET /api/v1/dashboard/summary` - Dashboard overview
- `GET /api/v1/dashboard/kpis` - Key performance indicators
- `GET /api/v1/inventory/low-stock/items` - Low stock alerts

## 🧪 Testing

### Backend Testing
```bash
cd supply-chain-command-center-backend
python -m pytest tests/ -v
python test_backend.py  # Custom functionality tests
```

### Frontend Testing
```bash
cd supply-chain-frontend
npm test
npm run test:e2e
```

## 🚀 Deployment

### Backend Deployment (Docker)
```bash
cd supply-chain-command-center-backend
docker build -t supply-chain-backend .
docker run -p 8000:8000 supply-chain-backend
```

### Frontend Deployment (Vercel/Netlify)
```bash
cd supply-chain-frontend
npm run build
npm start  # Production server
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for all new frontend code
- Add tests for new features
- Update documentation for API changes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **Next.js** - React framework for production
- **MongoDB** - Document database
- **Hugging Face** - Transformer models
- **Google Gemma** - LLM for forecasting
- **Tailwind CSS** - Utility-first CSS framework

## 📞 Support

- **Documentation**: [Project Wiki](https://github.com/YOUR_USERNAME/ai-supply-chain-platform/wiki)
- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/ai-supply-chain-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/ai-supply-chain-platform/discussions)

---

**Built with ❤️ for modern supply chain management**

# AI Supply Chain Backend

A FastAPI-based backend service for AI-powered supply chain management, featuring demand forecasting, inventory optimization, and logistics planning.

## Features

- 🔮 **Demand Forecasting**: Uses Facebook Prophet for time series forecasting
- 📦 **Inventory Management**: Smart inventory optimization and reorder recommendations
- 🚚 **Logistics Optimization**: Route planning and shipping cost calculation
- 🚀 **Fast API**: High-performance API built with FastAPI
- 📊 **AI-Powered**: Machine learning algorithms for supply chain optimization

## Project Structure

```
ai-supply-chain-backend/
├── main.py                 # FastAPI application entry point
├── routes/                 # API route modules
│   ├── demand.py          # Demand forecasting endpoints
│   ├── inventory.py       # Inventory management endpoints
│   └── logistics.py       # Logistics optimization endpoints
├── services/              # Business logic services
│   └── demand_forecasting.py  # Prophet-based demand forecasting
├── models/                # Data models (Pydantic/SQLAlchemy)
├── tests/                 # Unit and integration tests
├── docs/                  # Additional documentation
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-supply-chain-backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the development server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Demand Forecasting
- `POST /demand/forecast` - Generate demand forecast for next 7 days

### Inventory Management
- `GET /inventory/status` - Get current inventory status
- `POST /inventory/optimize` - Get inventory optimization recommendations

### Logistics
- `POST /logistics/optimize-routes` - Optimize delivery routes
- `POST /logistics/calculate-shipping` - Calculate shipping costs

## Example Usage

### Demand Forecasting
```bash
curl -X POST "http://localhost:8000/demand/forecast" \
     -H "Content-Type: application/json" \
     -d '{"past_sales": [100, 120, 95, 110, 130, 115, 140]}'
```

### Inventory Optimization
```bash
curl -X POST "http://localhost:8000/inventory/optimize" \
     -H "Content-Type: application/json" \
     -d '[{"product_id": "PROD-001", "current_stock": 50, "reorder_point": 100, "max_stock": 500}]'
```

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Prophet**: Time series forecasting by Meta
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Uvicorn**: ASGI server for running FastAPI

## Development

This project is designed for hackathon development with a focus on AI-powered supply chain optimization. The modular structure allows for easy extension and customization.

## License

This project is created for hackathon purposes.
