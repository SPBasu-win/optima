# 🚀 Complete Supply Chain Command Center Setup

This guide will help you set up both the FastAPI backend and Next.js frontend for your Supply Chain Command Center.

## 📁 Project Structure

```
ai-supply-chain-backend/
├── supply-chain-command-center-backend/  # FastAPI Backend
│   ├── main_dev.py                      # Simplified backend server
│   ├── requirements-simple.txt          # Python dependencies
│   ├── start-backend.ps1               # Backend startup script
│   └── test_backend.py                 # API test script
└── supply-chain-frontend/              # Next.js Frontend
    ├── src/                            # Source code
    ├── package.json                    # Node.js dependencies
    ├── start-frontend.ps1             # Frontend startup script
    └── tailwind.config.ts             # Tailwind CSS config
```

## 🔧 Prerequisites

✅ **Already Installed:**
- Python 3.11.9
- Node.js 24.7.0

## 🚀 Quick Start

### Step 1: Start the Backend

1. **Navigate to backend directory:**
   ```powershell
   cd ai-supply-chain-backend\supply-chain-command-center-backend
   ```

2. **Start the backend:**
   ```powershell
   .\start-backend.ps1
   ```
   
   This will:
   - Activate Python virtual environment
   - Start FastAPI server at http://localhost:8000
   - Provide API documentation at http://localhost:8000/docs

### Step 2: Start the Frontend

1. **Open a new terminal and navigate to frontend directory:**
   ```powershell
   cd ai-supply-chain-backend\supply-chain-frontend
   ```

2. **Start the frontend:**
   ```powershell
   .\start-frontend.ps1
   ```
   
   This will:
   - Install Node.js dependencies
   - Start Next.js dev server at http://localhost:3000

### Step 3: Access Your Application

- 🌐 **Frontend (Main App)**: http://localhost:3000
- 📚 **Backend API Docs**: http://localhost:8000/docs
- 🏥 **Backend Health Check**: http://localhost:8000/health

## 🔍 Testing the Setup

### Test Backend API
```powershell
# In the backend directory
python test_backend.py
```

### Test Frontend Connection
1. Open http://localhost:3000 in your browser
2. You should see the Supply Chain Dashboard
3. Check browser console for any API connection issues

## 📊 What You'll See

### Dashboard Features:
- **KPI Cards**: Total items, inventory value, low stock alerts
- **Navigation**: Dashboard, Inventory, Forecasting, Suppliers
- **Low Stock Alerts**: Items below minimum threshold
- **Real-time Data**: Connected to your FastAPI backend

### Sample Data Included:
- **Dell Inspiron 15**: 25 units in stock
- **Wireless Mouse**: 2 units (LOW STOCK)  
- **Office Desk**: 15 units in stock

## 🛠️ Development Commands

### Backend Commands:
```powershell
# Start backend
uvicorn main_dev:app --host 0.0.0.0 --port 8000 --reload

# Test API
python test_backend.py

# View API documentation
# Visit: http://localhost:8000/docs
```

### Frontend Commands:
```powershell
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 🔧 Configuration

### Backend Configuration:
- **API Base URL**: http://localhost:8000
- **Database**: In-memory (no external DB needed)
- **Sample Data**: Pre-loaded inventory items

### Frontend Configuration:
- **API Endpoint**: http://localhost:8000/api/v1
- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query

## 📁 Key Files

### Backend:
- `main_dev.py` - Simplified FastAPI application
- `requirements-simple.txt` - Python dependencies
- `start-backend.ps1` - Backend startup script

### Frontend:
- `src/app/page.tsx` - Main dashboard page
- `src/lib/api.ts` - API service layer
- `src/components/navigation.tsx` - Navigation component
- `package.json` - Node.js dependencies

## 🌟 Features Available

### ✅ Implemented:
- **Dashboard**: KPIs, summary stats, low stock alerts
- **API Integration**: Full CRUD operations for inventory
- **Navigation**: Multi-page navigation structure
- **Responsive Design**: Mobile-friendly interface
- **Error Handling**: Graceful error messages
- **Loading States**: Loading spinners and states

### 🚧 Ready for Extension:
- **Inventory Management**: Add/edit/delete items
- **Forecasting**: Demand prediction charts
- **Suppliers**: Supplier management interface
- **Analytics**: Advanced reporting and charts

## 🔧 Troubleshooting

### Backend Issues:
1. **Port 8000 in use**: Change port in start command
2. **Python not found**: Ensure Python 3.11+ is installed
3. **Module errors**: Check virtual environment activation

### Frontend Issues:
1. **Port 3000 in use**: Next.js will auto-assign different port
2. **API connection errors**: Ensure backend is running first
3. **Node.js errors**: Try `npm install` to reinstall dependencies

### Connection Issues:
1. **CORS Errors**: Backend is configured for localhost:3000
2. **API Not Found**: Check backend is running at localhost:8000
3. **Timeout Errors**: Increase timeout in `src/lib/api.ts`

## 🚀 Next Steps

1. **Add More Pages**: Implement inventory management, forecasting
2. **Database**: Upgrade to MongoDB/PostgreSQL for persistence
3. **Authentication**: Add user login and permissions
4. **Deployment**: Deploy to cloud platforms
5. **Real ML**: Integrate Prophet for real demand forecasting

## 📞 Support

If you encounter issues:
1. Check both servers are running (backend:8000, frontend:3000)
2. Review browser console for frontend errors
3. Check terminal output for backend errors
4. Test API endpoints directly at http://localhost:8000/docs

---

**🎉 Congratulations! You now have a complete Supply Chain Management system running locally!**
