export interface InventoryItem {
  sku: string;
  name: string;
  description?: string;
  category: string;
  current_stock: number;
  minimum_stock: number;
  cost_price: number;
  selling_price: number;
  warehouse_id: string;
  supplier_id: string;
  created_at: string;
  updated_at: string;
}

export interface InventoryItemCreate {
  sku: string;
  name: string;
  description?: string;
  category: string;
  current_stock: number;
  minimum_stock: number;
  cost_price: number;
  selling_price: number;
}

export interface DashboardSummary {
  total_items: number;
  low_stock_items: number;
  total_value: number;
  categories: number;
}

export interface DashboardKPIs {
  total_inventory_value: number;
  total_items: number;
  low_stock_alerts: number;
  categories_count: number;
  avg_stock_level: number;
}

export interface LowStockResponse {
  count: number;
  items: InventoryItem[];
}

export interface ForecastData {
  day: number;
  predicted_demand: number;
  date?: string;
}

export interface ForecastResponse {
  sku: string;
  forecast_days: number;
  forecast: ForecastData[];
  total_predicted_demand: number;
  note?: string;
}

export interface Supplier {
  id: string;
  name: string;
  category: string;
}
