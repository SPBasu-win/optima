# Connecting Your Next.js Frontend to the Supply Chain Backend

## Backend URL
Your FastAPI backend will be running at: `http://localhost:8000`

## 1. Install Required Dependencies

In your Next.js project:

```bash
npm install axios
# or
npm install @tanstack/react-query axios  # for better API management
```

## 2. Create API Service Layer

Create `lib/api.js` or `lib/api.ts`:

```javascript
// lib/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inventory API functions
export const inventoryAPI = {
  // Get all inventory items
  getAll: (params = {}) => api.get('/inventory/', { params }),
  
  // Get single item by SKU
  getById: (sku) => api.get(`/inventory/${sku}`),
  
  // Create new item
  create: (itemData) => api.post('/inventory/', itemData),
  
  // Update item
  update: (sku, updateData) => api.put(`/inventory/${sku}`, updateData),
  
  // Delete item
  delete: (sku) => api.delete(`/inventory/${sku}`),
  
  // Get low stock items
  getLowStock: () => api.get('/inventory/low-stock/items'),
};

// Dashboard API functions
export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/summary'),
  getKPIs: () => api.get('/dashboard/kpis'),
};

// Forecasting API functions
export const forecastingAPI = {
  getDemandForecast: (sku, days = 30) => 
    api.get(`/forecasting/demand/${sku}?days=${days}`),
};

// Suppliers API
export const suppliersAPI = {
  getAll: () => api.get('/suppliers/'),
};

export default api;
```

## 3. Example React Components

### Dashboard Component

```jsx
// components/Dashboard.jsx
import { useState, useEffect } from 'react';
import { dashboardAPI } from '../lib/api';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [kpis, setKPIs] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [summaryRes, kpisRes] = await Promise.all([
          dashboardAPI.getSummary(),
          dashboardAPI.getKPIs()
        ]);
        
        setSummary(summaryRes.data);
        setKPIs(kpisRes.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <h1>Supply Chain Dashboard</h1>
      
      <div className="kpi-cards">
        <div className="card">
          <h3>Total Items</h3>
          <p className="kpi-value">{summary?.total_items || 0}</p>
        </div>
        
        <div className="card">
          <h3>Low Stock Alerts</h3>
          <p className="kpi-value alert">{summary?.low_stock_items || 0}</p>
        </div>
        
        <div className="card">
          <h3>Total Value</h3>
          <p className="kpi-value">${summary?.total_value?.toFixed(2) || '0.00'}</p>
        </div>
        
        <div className="card">
          <h3>Categories</h3>
          <p className="kpi-value">{summary?.categories || 0}</p>
        </div>
      </div>
    </div>
  );
}
```

### Inventory List Component

```jsx
// components/InventoryList.jsx
import { useState, useEffect } from 'react';
import { inventoryAPI } from '../lib/api';

export default function InventoryList() {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    category: '',
    low_stock_only: false
  });

  useEffect(() => {
    fetchInventory();
  }, [filters]);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      const response = await inventoryAPI.getAll(filters);
      setInventory(response.data);
    } catch (error) {
      console.error('Error fetching inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  if (loading) return <div>Loading inventory...</div>;

  return (
    <div className="inventory-list">
      <h2>Inventory Management</h2>
      
      {/* Filters */}
      <div className="filters">
        <select 
          value={filters.category} 
          onChange={(e) => handleFilterChange('category', e.target.value)}
        >
          <option value="">All Categories</option>
          <option value="Electronics">Electronics</option>
          <option value="Furniture">Furniture</option>
        </select>
        
        <label>
          <input
            type="checkbox"
            checked={filters.low_stock_only}
            onChange={(e) => handleFilterChange('low_stock_only', e.target.checked)}
          />
          Show Low Stock Only
        </label>
      </div>

      {/* Inventory Table */}
      <table className="inventory-table">
        <thead>
          <tr>
            <th>SKU</th>
            <th>Name</th>
            <th>Category</th>
            <th>Stock</th>
            <th>Min Stock</th>
            <th>Price</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {inventory.map((item) => (
            <tr key={item.sku}>
              <td>{item.sku}</td>
              <td>{item.name}</td>
              <td>{item.category}</td>
              <td>{item.current_stock}</td>
              <td>{item.minimum_stock}</td>
              <td>${item.selling_price}</td>
              <td className={item.current_stock <= item.minimum_stock ? 'low-stock' : 'in-stock'}>
                {item.current_stock <= item.minimum_stock ? 'Low Stock' : 'In Stock'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Add New Item Form

```jsx
// components/AddInventoryItem.jsx
import { useState } from 'react';
import { inventoryAPI } from '../lib/api';

export default function AddInventoryItem({ onSuccess }) {
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    description: '',
    category: 'Electronics',
    current_stock: 0,
    minimum_stock: 0,
    cost_price: 0,
    selling_price: 0
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await inventoryAPI.create(formData);
      alert('Item added successfully!');
      setFormData({
        sku: '',
        name: '',
        description: '',
        category: 'Electronics',
        current_stock: 0,
        minimum_stock: 0,
        cost_price: 0,
        selling_price: 0
      });
      onSuccess?.();
    } catch (error) {
      console.error('Error adding item:', error);
      alert('Error adding item: ' + error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name.includes('stock') || name.includes('price') ? Number(value) : value
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="add-item-form">
      <h3>Add New Inventory Item</h3>
      
      <div className="form-group">
        <label>SKU:</label>
        <input
          type="text"
          name="sku"
          value={formData.sku}
          onChange={handleChange}
          required
        />
      </div>

      <div className="form-group">
        <label>Name:</label>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
        />
      </div>

      <div className="form-group">
        <label>Category:</label>
        <select name="category" value={formData.category} onChange={handleChange}>
          <option value="Electronics">Electronics</option>
          <option value="Furniture">Furniture</option>
          <option value="Clothing">Clothing</option>
        </select>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Current Stock:</label>
          <input
            type="number"
            name="current_stock"
            value={formData.current_stock}
            onChange={handleChange}
            min="0"
            required
          />
        </div>

        <div className="form-group">
          <label>Minimum Stock:</label>
          <input
            type="number"
            name="minimum_stock"
            value={formData.minimum_stock}
            onChange={handleChange}
            min="0"
            required
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Cost Price:</label>
          <input
            type="number"
            name="cost_price"
            value={formData.cost_price}
            onChange={handleChange}
            min="0"
            step="0.01"
            required
          />
        </div>

        <div className="form-group">
          <label>Selling Price:</label>
          <input
            type="number"
            name="selling_price"
            value={formData.selling_price}
            onChange={handleChange}
            min="0"
            step="0.01"
            required
          />
        </div>
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Adding...' : 'Add Item'}
      </button>
    </form>
  );
}
```

## 4. Using React Query (Recommended)

For better API management, use React Query:

```jsx
// hooks/useInventory.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryAPI } from '../lib/api';

export function useInventory(filters = {}) {
  return useQuery({
    queryKey: ['inventory', filters],
    queryFn: () => inventoryAPI.getAll(filters).then(res => res.data),
    staleTime: 30000, // 30 seconds
  });
}

export function useAddInventoryItem() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: inventoryAPI.create,
    onSuccess: () => {
      // Invalidate inventory queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });
}
```

## 5. Environment Variables

Create `.env.local` in your Next.js project:

```env
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Then update your API service:

```javascript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
```

## 6. Basic CSS for Styling

```css
/* styles/dashboard.css */
.dashboard {
  padding: 2rem;
}

.kpi-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.card {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
}

.kpi-value {
  font-size: 2rem;
  font-weight: bold;
  color: #007bff;
}

.kpi-value.alert {
  color: #dc3545;
}

.inventory-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.inventory-table th,
.inventory-table td {
  border: 1px solid #dee2e6;
  padding: 0.75rem;
  text-align: left;
}

.inventory-table th {
  background-color: #f8f9fa;
  font-weight: bold;
}

.low-stock {
  color: #dc3545;
  font-weight: bold;
}

.in-stock {
  color: #28a745;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  align-items: center;
}

.add-item-form {
  max-width: 600px;
  margin: 2rem 0;
  padding: 1.5rem;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background: #f8f9fa;
}

.form-group {
  margin-bottom: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: bold;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

button:hover {
  background-color: #0056b3;
}

button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}
```

This setup gives you a complete connection between your Next.js frontend and the FastAPI backend!
