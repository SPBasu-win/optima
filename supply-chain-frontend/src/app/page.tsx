'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryAPI, enhancedInventoryAPI, notificationsAPI } from '@/lib/api';
import { Search, Filter, Plus, Edit, Trash2, RefreshCw, Check, X, History } from 'lucide-react';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import type { InventoryItem } from '@/types';

// Helper function to determine stock status
function getStockStatus(item: InventoryItem) {
  if (item.current_stock === 0) return 'out-of-stock';
  if (item.current_stock <= item.minimum_stock) return 'low-stock';
  return 'in-stock';
}

// Helper function to get status display
function getStatusDisplay(status: string) {
  switch (status) {
    case 'out-of-stock': return 'Out of Stock';
    case 'low-stock': return 'Low Stock';
    case 'in-stock': return 'In Stock';
    default: return 'Unknown';
  }
}

function StatusBadge({ status }: { status: string }) {
  const styles = {
    'in-stock': 'status-delivered',
    'low-stock': 'status-pending',
    'out-of-stock': 'status-out-of-stock',
  };

  return (
    <span className={styles[status as keyof typeof styles]}>
      {getStatusDisplay(status)}
    </span>
  );
}

function InlineStockEditor({ item, onUpdate }: { 
  item: InventoryItem; 
  onUpdate: (sku: string, newStock: number, reason: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [newStock, setNewStock] = useState(item.current_stock);
  const [reason, setReason] = useState('');

  const handleSave = () => {
    if (newStock !== item.current_stock) {
      onUpdate(item.sku, newStock, reason || 'Manual adjustment');
    }
    setIsEditing(false);
    setReason('');
  };

  const handleCancel = () => {
    setNewStock(item.current_stock);
    setReason('');
    setIsEditing(false);
  };

  if (!isEditing) {
    return (
      <div 
        className="flex items-center space-x-1 cursor-pointer hover:bg-gray-700 px-2 py-1 rounded"
        onClick={() => setIsEditing(true)}
        title="Click to edit stock"
      >
        <span>{item.current_stock} / {item.minimum_stock}</span>
        <Edit className="w-3 h-3 text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center space-x-1">
        <input
          type="number"
          value={newStock}
          onChange={(e) => setNewStock(Number(e.target.value))}
          className="w-16 px-2 py-1 text-sm bg-gray-700 border border-gray-600 rounded text-white"
          min="0"
          autoFocus
        />
        <span className="text-gray-400">/ {item.minimum_stock}</span>
        <button
          onClick={handleSave}
          className="text-green-400 hover:text-green-300"
          title="Save"
        >
          <Check className="w-4 h-4" />
        </button>
        <button
          onClick={handleCancel}
          className="text-red-400 hover:text-red-300"
          title="Cancel"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <input
        type="text"
        placeholder="Reason (optional)"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        className="w-full px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400"
      />
    </div>
  );
}

function EditItemModal({ isOpen, onClose, onUpdate, item }: {
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (sku: string, updates: any) => void;
  item: InventoryItem | null;
}) {
  const [formData, setFormData] = useState({
    name: '',
    category: 'Electronics',
    current_stock: 0,
    minimum_stock: 0,
    cost_price: 0,
    selling_price: 0,
    description: '',
  });

  // Update form data when item changes
  useState(() => {
    if (item) {
      setFormData({
        name: item.name,
        category: item.category,
        current_stock: item.current_stock,
        minimum_stock: item.minimum_stock,
        cost_price: item.cost_price,
        selling_price: item.selling_price,
        description: item.description || '',
      });
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (item) {
      onUpdate(item.sku, formData);
    }
    onClose();
  };

  if (!isOpen || !item) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-[#1a1a1a] p-6 rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-semibold text-white mb-4">Edit {item.name}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
              rows={2}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Category</label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({...formData, category: e.target.value})}
              className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
            >
              <option value="Electronics">Electronics</option>
              <option value="Furniture">Furniture</option>
              <option value="Clothing">Clothing</option>
              <option value="Books">Books</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Current Stock</label>
              <input
                type="number"
                value={formData.current_stock}
                onChange={(e) => setFormData({...formData, current_stock: Number(e.target.value)})}
                className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Min Stock</label>
              <input
                type="number"
                value={formData.minimum_stock}
                onChange={(e) => setFormData({...formData, minimum_stock: Number(e.target.value)})}
                className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
                min="0"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Cost Price</label>
              <input
                type="number"
                value={formData.cost_price}
                onChange={(e) => setFormData({...formData, cost_price: Number(e.target.value)})}
                className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
                min="0"
                step="0.01"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Selling Price</label>
              <input
                type="number"
                value={formData.selling_price}
                onChange={(e) => setFormData({...formData, selling_price: Number(e.target.value)})}
                className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
                min="0"
                step="0.01"
              />
            </div>
          </div>
          <div className="flex space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
            >
              Update Item
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AddItemModal({ isOpen, onClose, onAdd }: {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (item: any) => void;
}) {
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    category: 'Electronics',
    current_stock: 0,
    minimum_stock: 0,
    cost_price: 0,
    selling_price: 0
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd(formData);
    setFormData({
      sku: '',
      name: '',
      category: 'Electronics',
      current_stock: 0,
      minimum_stock: 0,
      cost_price: 0,
      selling_price: 0
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-[#1a1a1a] p-6 rounded-lg w-full max-w-md">
        <h2 className="text-xl font-semibold text-white mb-4">Add New Item</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">SKU</label>
            <input
              type="text"
              value={formData.sku}
              onChange={(e) => setFormData({...formData, sku: e.target.value})}
              className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Current Stock</label>
              <input
                type="number"
                value={formData.current_stock}
                onChange={(e) => setFormData({...formData, current_stock: Number(e.target.value)})}
                className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Min Stock</label>
              <input
                type="number"
                value={formData.minimum_stock}
                onChange={(e) => setFormData({...formData, minimum_stock: Number(e.target.value)})}
                className="w-full p-2 bg-[#111111] border border-gray-600 rounded text-white"
                min="0"
              />
            </div>
          </div>
          <div className="flex space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
            >
              Add Item
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Overview() {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  
  const queryClient = useQueryClient();
  
  // Show notification helper
  const showNotification = (message: string) => {
    setNotification(message);
    setTimeout(() => setNotification(null), 3000);
  };

  // Fetch inventory data
  const { data: inventoryItems, isLoading, error, refetch } = useQuery({
    queryKey: ['inventory-overview'],
    queryFn: () => inventoryAPI.getAll({}),
  });

  // Add new item mutation
  const addItemMutation = useMutation({
    mutationFn: inventoryAPI.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['inventory-overview'] });
      showNotification(`Successfully added ${data.name}`);
    },
    onError: (error: any) => {
      showNotification(`Error adding item: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Update item mutation
  const updateItemMutation = useMutation({
    mutationFn: ({ sku, updates }: { sku: string; updates: any }) =>
      inventoryAPI.update(sku, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['inventory-overview'] });
      showNotification(`Successfully updated ${data.name}`);
      setShowEditModal(false);
    },
    onError: (error: any) => {
      showNotification(`Error updating item: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Stock update mutation
  const updateStockMutation = useMutation({
    mutationFn: ({ sku, newStock, reason }: { sku: string; newStock: number; reason: string }) =>
      enhancedInventoryAPI.updateStock(sku, newStock, reason),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['inventory-overview'] });
      showNotification(data.message);
    },
    onError: (error: any) => {
      showNotification(`Error updating stock: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Delete item mutation
  const deleteItemMutation = useMutation({
    mutationFn: inventoryAPI.delete,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['inventory-overview'] });
      showNotification(`Successfully deleted ${data.deleted_item.name}`);
    },
    onError: (error: any) => {
      showNotification(`Error deleting item: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Filter items based on search and filters
  const filteredItems = inventoryItems?.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.sku.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !categoryFilter || item.category === categoryFilter;
    const itemStatus = getStockStatus(item);
    const matchesStatus = !statusFilter || itemStatus === statusFilter;
    
    return matchesSearch && matchesCategory && matchesStatus;
  }) || [];

  if (isLoading) {
    return <LoadingSpinner message="Loading inventory..." />;
  }

  if (error) {
    return <ErrorMessage message="Failed to load inventory data" onRetry={() => refetch()} />;
  }

  const uniqueCategories = [...new Set(inventoryItems?.map(item => item.category) || [])];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-white">Overview</h1>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-gray-300 hover:text-white flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 flex items-center"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Item
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search by SKU or Name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-orange-500"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-4 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white"
        >
          <option value="">All Categories</option>
          {uniqueCategories.map(category => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white"
        >
          <option value="">All Status</option>
          <option value="in-stock">In Stock</option>
          <option value="low-stock">Low Stock</option>
          <option value="out-of-stock">Out of Stock</option>
        </select>
      </div>

      {/* Inventory Table */}
      <div className="bg-[#1a1a1a] rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                SKU
              </th>
              <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                Item Name
              </th>
              <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                Category
              </th>
              <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                Stock
              </th>
              <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                Price
              </th>
              <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item, index) => {
              const status = getStockStatus(item);
              return (
                <tr 
                  key={item.sku} 
                  className={`border-b border-gray-700 hover:bg-gray-800/50 ${
                    index % 2 === 0 ? 'bg-[#111111]' : 'bg-[#1a1a1a]'
                  }`}
                >
                  <td className="py-4 px-6 text-white font-medium">
                    {item.sku}
                  </td>
                  <td className="py-4 px-6 text-gray-300">
                    {item.name}
                  </td>
                  <td className="py-4 px-6 text-gray-300">
                    {item.category}
                  </td>
                  <td className="py-4 px-6 text-gray-300">
                    <InlineStockEditor 
                      item={item}
                      onUpdate={(sku, newStock, reason) => 
                        updateStockMutation.mutate({ sku, newStock, reason })
                      }
                    />
                  </td>
                  <td className="py-4 px-6 text-gray-300">
                    ${item.selling_price.toFixed(2)}
                  </td>
                  <td className="py-4 px-6">
                    <StatusBadge status={status} />
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          setSelectedItem(item);
                          setShowEditModal(true);
                        }}
                        className="text-gray-400 hover:text-orange-500"
                        title="Edit"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => deleteItemMutation.mutate(item.sku)}
                        className="text-gray-400 hover:text-red-500"
                        title="Delete"
                        disabled={deleteItemMutation.isPending}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {filteredItems.length === 0 && (
        <div className="text-center py-8 text-gray-400">
          No items found matching your criteria.
        </div>
      )}

      {/* Notification */}
      {notification && (
        <div className="fixed top-4 right-4 bg-orange-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in">
          {notification}
        </div>
      )}

      {/* Add Item Modal */}
      <AddItemModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={(item) => addItemMutation.mutate(item)}
      />

      {/* Edit Item Modal */}
      <EditItemModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedItem(null);
        }}
        onUpdate={(sku, updates) => updateItemMutation.mutate({ sku, updates })}
        item={selectedItem}
      />
    </div>
  );
}
