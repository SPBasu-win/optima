# 🚀 Optima AI Supply Chain Platform - Setup Guide

**Complete setup instructions for developers wanting to run this project locally**

## 📋 Prerequisites

Before starting, ensure you have the following installed:

### Required Software:
- **Python 3.11+** - [Download from python.org](https://www.python.org/downloads/)
- **Node.js 18+** - [Download from nodejs.org](https://nodejs.org/)
- **Git** - [Download from git-scm.com](https://git-scm.com/)

### Optional (for full AI features):
- **MongoDB 7.0+** - [Download from mongodb.com](https://www.mongodb.com/try/download/community)
- **Ollama** - [Download from ollama.com](https://ollama.com/) (for Gemma AI models)

---

## 🚀 Quick Start (5 minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/SPBasu-win/optima.git
cd optima
```

### Step 2: Backend Setup

**For Windows PowerShell:**
```powershell
# Navigate to backend directory
cd supply-chain-command-center-backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements-simple.txt

# Start the backend server
.\start-backend.ps1
```

**For macOS/Linux:**
```bash
# Navigate to backend directory
cd supply-chain-command-center-backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-simple.txt

# Start the backend server
uvicorn main_dev:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Frontend Setup (New Terminal)

**For Windows PowerShell:**
```powershell
# Navigate to frontend directory (from project root)
cd supply-chain-frontend

# Start the frontend
.\start-frontend.ps1
```

**For macOS/Linux:**
```bash
# Navigate to frontend directory (from project root)
cd supply-chain-frontend

# Install dependencies and start
npm install
npm run dev
```

### Step 4: Access Your Application

- 🌐 **Main Application**: http://localhost:3000
- 📚 **API Documentation**: http://localhost:8000/docs
- 🏥 **API Health Check**: http://localhost:8000/health

---

## 🔧 Detailed Setup Instructions

### Backend Setup Details

The backend is a **FastAPI** application with AI-powered features:

1. **Navigate to backend directory:**
   ```bash
   cd supply-chain-command-center-backend
   ```

2. **Create Python virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   # For quick start (basic features)
   pip install -r requirements-simple.txt
   
   # For full AI features (larger download)
   pip install -r requirements.txt
   ```

4. **Start the backend server:**
   ```bash
   # Using the provided script (Windows)
   .\start-backend.ps1
   
   # Or manually
   uvicorn main_dev:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup Details

The frontend is a **Next.js** application with React and TypeScript:

1. **Navigate to frontend directory:**
   ```bash
   cd supply-chain-frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   # Using the provided script (Windows)
   .\start-frontend.ps1
   
   # Or manually
   npm run dev
   ```

---

## 🧪 Testing Your Setup

### 1. Test Backend API
```bash
# In the backend directory
python test_backend.py
```

### 2. Test Frontend Connection
1. Open http://localhost:3000 in your browser
2. You should see the Supply Chain Dashboard
3. Check that KPI cards load with sample data
4. Verify navigation works between different pages

### 3. Test API Endpoints
Visit http://localhost:8000/docs to interact with the API directly

---

## 📊 What You'll See

### Dashboard Features:
- **📈 KPI Cards**: Total inventory items, total value, low stock alerts
- **🧭 Navigation**: Dashboard, Data Import, Demand Forecasting, Inventory Management
- **⚠️ Low Stock Alerts**: Items below minimum stock threshold
- **📱 Responsive Design**: Works on desktop, tablet, and mobile

### Sample Data Included:
- **Dell Inspiron 15** (25 units - Good stock)
- **Wireless Mouse** (2 units - LOW STOCK alert)
- **Office Desk** (15 units - Good stock)

---

## 🎨 Key Features Available

### ✅ Currently Working:
- **Real-time Dashboard** with live KPIs
- **Inventory Management** with CRUD operations
- **Data Import** with CSV/Excel file upload
- **AI-powered Data Cleaning** using T5 transformers
- **Low Stock Monitoring** with automated alerts
- **Demand Forecasting** with Prophet and Gemma AI
- **REST API** with FastAPI and automatic documentation
- **Modern UI** with Next.js, TypeScript, and Tailwind CSS

### 🚧 Ready for Extension:
- **Advanced Analytics** and reporting
- **Supplier Management** system
- **Logistics Optimization** with route planning
- **Multi-warehouse Support**
- **User Authentication** and permissions
- **Real-time Notifications**

---

## 🛠️ Development Commands

### Backend Commands:
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Start development server
uvicorn main_dev:app --reload --host 0.0.0.0 --port 8000

# Run tests
python test_backend.py
pytest tests/ -v

# Install full AI dependencies
pip install -r requirements.txt
```

### Frontend Commands:
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
npm start

# Run tests
npm test
npm run test:e2e

# Lint code
npm run lint
```

---

## 🤖 AI Features Setup (Optional)

### For Full AI Capabilities:

1. **Install full Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Ollama (for Gemma AI):**
   - Download from https://ollama.com
   - Install Gemma model: `ollama pull gemma:2b`

3. **MongoDB (for persistence):**
   - Install MongoDB Community Edition
   - Start MongoDB service
   - Update connection string in backend configuration

---

## 🔧 Configuration Options

### Backend Configuration:
Create `.env` file in `supply-chain-command-center-backend/`:
```env
# Database
MONGODB_URL=mongodb://localhost:27017/supply_chain_db

# API Settings
API_V1_STR=/api/v1
PROJECT_NAME=Optima Supply Chain Platform
SECRET_KEY=your-secret-key-here

# AI Models
OLLAMA_BASE_URL=http://localhost:11434
HUGGINGFACE_CACHE_DIR=./models
```

### Frontend Configuration:
Create `.env.local` file in `supply-chain-frontend/`:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Optima Supply Chain Platform
```

---

## 🚨 Troubleshooting

### Common Issues:

#### Backend Won't Start:
- **Python not found**: Ensure Python 3.11+ is installed and in PATH
- **Port 8000 in use**: Kill existing process or change port
- **Virtual environment issues**: Delete `venv` folder and recreate
- **Dependencies missing**: Run `pip install -r requirements-simple.txt`

#### Frontend Won't Start:
- **Node.js not found**: Install Node.js 18+ from nodejs.org
- **Port 3000 in use**: Next.js will auto-assign a different port
- **Dependencies issues**: Delete `node_modules` and run `npm install`
- **Build errors**: Check Node.js version compatibility

#### Connection Issues:
- **API not reachable**: Ensure backend is running at localhost:8000
- **CORS errors**: Backend is pre-configured for localhost:3000
- **Data not loading**: Check browser console for API errors

### Getting Help:
1. Check both servers are running (backend:8000, frontend:3000)
2. Review terminal output for error messages
3. Test API endpoints at http://localhost:8000/docs
4. Check browser console for frontend issues

---

## 📁 Project Structure

```
optima/
├── supply-chain-command-center-backend/    # FastAPI Backend
│   ├── app/                               # Application code
│   ├── main_dev.py                        # Development server
│   ├── requirements-simple.txt           # Basic dependencies
│   ├── requirements.txt                  # Full AI dependencies
│   ├── start-backend.ps1                # Windows startup script
│   └── test_backend.py                   # API tests
│
├── supply-chain-frontend/                # Next.js Frontend
│   ├── src/                             # Source code
│   ├── public/                          # Static files
│   ├── package.json                     # Node dependencies
│   ├── start-frontend.ps1              # Windows startup script
│   └── tailwind.config.ts              # Styling config
│
├── README.md                            # Main documentation
├── COMPLETE_SETUP_GUIDE.md             # Detailed setup guide
└── SETUP_FOR_OTHERS.md                 # This file
```

---

## 🌟 Next Steps

After successful setup:

1. **Explore the Dashboard** - Navigate through different sections
2. **Test Data Import** - Upload a CSV file to see AI data cleaning
3. **Try Demand Forecasting** - Generate predictions for inventory items
4. **Customize the UI** - Modify components in `src/components/`
5. **Extend the API** - Add new endpoints in `app/api/v1/endpoints/`
6. **Deploy to Cloud** - Use Docker for containerized deployment

---

## 📞 Support & Contributing

### Need Help?
- **Documentation**: Check the README.md for detailed technical docs
- **API Reference**: Visit http://localhost:8000/docs when running
- **Issues**: Report bugs or request features on GitHub

### Want to Contribute?
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

---

## 🎉 Success!

If you can see the dashboard at http://localhost:3000 with live data from the API, you're all set! 

**You now have a complete AI-powered supply chain management platform running locally.**

**Built with ❤️ using FastAPI, Next.js, and modern AI technologies**
