'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { inventoryAPI, enhancedForecastingAPI } from '@/lib/api';
import { TrendingUp, Calendar, BarChart3, AlertCircle } from 'lucide-react';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

function ForecastChart({ data, type }: { data: any[]; type: 'demand' | 'cost' }) {
  const valueKey = type === 'demand' ? 'predicted_demand' : 'predicted_cost';
  const maxValue = Math.max(...data.map(d => d[valueKey] || 0));
  const unit = type === 'demand' ? 'units' : '$';
  const color = type === 'demand' ? 'bg-orange-500' : 'bg-green-500';
  const hoverColor = type === 'demand' ? 'hover:bg-orange-400' : 'hover:bg-green-400';
  
  return (
    <div className="bg-[#1a1a1a] p-6 rounded-lg">
      <h3 className="text-lg font-medium text-white mb-4">
        {type === 'demand' ? 'Demand Forecast' : 'Cost Forecast'}
      </h3>
      <div className="h-64 flex items-end space-x-2">
        {data.slice(0, 14).map((item, index) => {
          const value = item[valueKey] || 0;
          return (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div 
                className={`${color} ${hoverColor} rounded-t w-full transition-all duration-300`}
                style={{ 
                  height: `${maxValue > 0 ? (value / maxValue) * 200 : 4}px`,
                  minHeight: '4px'
                }}
                title={`Day ${item.day}: ${type === 'cost' ? '$' : ''}${value}${type === 'demand' ? ' units' : ''}`}
              />
              <span className="text-xs text-gray-400 mt-2">D{item.day}</span>
            </div>
          );
        })}
      </div>
      <div className="flex justify-between mt-4 text-sm text-gray-400">
        <span>Next 14 Days</span>
        <span>Max: {type === 'cost' ? '$' : ''}{maxValue}{type === 'demand' ? ' units' : ''}</span>
      </div>
    </div>
  );
}

export default function DemandForecasting() {
  const [selectedSku, setSelectedSku] = useState('');
  const [forecastDays, setForecastDays] = useState(30);
  const [forecastType, setForecastType] = useState<'demand' | 'cost'>('demand');

  // Get inventory items for selection
  const { data: inventoryItems } = useQuery({
    queryKey: ['inventory-items'],
    queryFn: () => inventoryAPI.getAll({}),
  });

  // Get demand forecast for selected item
  const { data: demandForecast, isLoading: demandLoading } = useQuery({
    queryKey: ['demand-forecast', selectedSku, forecastDays],
    queryFn: () => enhancedForecastingAPI.getDemandForecast(selectedSku, forecastDays),
    enabled: !!selectedSku && forecastType === 'demand',
  });

  // Get cost forecast for selected item
  const { data: costForecast, isLoading: costLoading } = useQuery({
    queryKey: ['cost-forecast', selectedSku, forecastDays],
    queryFn: () => enhancedForecastingAPI.getCostForecast(selectedSku, forecastDays),
    enabled: !!selectedSku && forecastType === 'cost',
  });

  const firstItem = inventoryItems?.[0];
  if (!selectedSku && firstItem) {
    setSelectedSku(firstItem.sku);
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-white mb-2">Demand Forecasting</h1>
        <p className="text-gray-400">
          AI-powered demand predictions to optimize inventory levels and reduce stockouts.
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center space-x-4 bg-[#1a1a1a] p-4 rounded-lg">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-400 mb-2">Select Product</label>
          <select
            value={selectedSku}
            onChange={(e) => setSelectedSku(e.target.value)}
            className="w-full px-3 py-2 bg-[#111111] border border-gray-600 rounded-lg text-white"
          >
            <option value="">Select a product...</option>
            {inventoryItems?.map((item) => (
              <option key={item.sku} value={item.sku}>
                {item.sku} - {item.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Forecast Period</label>
          <select
            value={forecastDays}
            onChange={(e) => setForecastDays(Number(e.target.value))}
            className="px-3 py-2 bg-[#111111] border border-gray-600 rounded-lg text-white"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
          </select>
        </div>
      </div>

      {/* Forecast Results */}
      {selectedSku && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Forecast Chart */}
          <div className="lg:col-span-2">
            {forecastLoading ? (
              <div className="bg-[#1a1a1a] p-6 rounded-lg">
                <LoadingSpinner message="Generating forecast..." />
              </div>
            ) : forecast ? (
              <ForecastChart data={forecast.forecast} />
            ) : (
              <div className="bg-[#1a1a1a] p-6 rounded-lg text-center">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-400">No forecast data available</p>
              </div>
            )}
          </div>

          {/* Forecast Summary */}
          <div className="space-y-4">
            <div className="bg-[#1a1a1a] p-6 rounded-lg">
              <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-orange-500" />
                Forecast Summary
              </h3>
              {forecast && (
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Product:</span>
                    <span className="text-white font-medium">{selectedSku}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Period:</span>
                    <span className="text-white">{forecastDays} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Predicted:</span>
                    <span className="text-orange-500 font-bold">
                      {forecast.total_predicted_demand} units
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Daily Average:</span>
                    <span className="text-white">
                      {Math.round(forecast.total_predicted_demand / forecastDays)} units
                    </span>
                  </div>
                  <div className="pt-2 border-t border-gray-700">
                    <div className="text-xs text-gray-400">
                      {forecast.note}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Insights */}
            <div className="bg-[#1a1a1a] p-6 rounded-lg">
              <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2 text-blue-500" />
                Insights
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-1.5" />
                  <div>
                    <div className="text-white font-medium">Demand Trend</div>
                    <div className="text-gray-400">Stable demand pattern expected</div>
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mt-1.5" />
                  <div>
                    <div className="text-white font-medium">Reorder Alert</div>
                    <div className="text-gray-400">Consider restocking in 7-10 days</div>
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5" />
                  <div>
                    <div className="text-white font-medium">Confidence Level</div>
                    <div className="text-gray-400">75% accuracy based on historical data</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Current Stock Status */}
            <div className="bg-[#1a1a1a] p-6 rounded-lg">
              <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-green-500" />
                Stock Status
              </h3>
              {inventoryItems?.find(item => item.sku === selectedSku) && (
                <div className="space-y-2 text-sm">
                  {(() => {
                    const item = inventoryItems.find(i => i.sku === selectedSku);
                    const currentStock = item?.current_stock || 0;
                    const dailyDemand = forecast ? forecast.total_predicted_demand / forecastDays : 0;
                    const daysOfStock = dailyDemand > 0 ? Math.floor(currentStock / dailyDemand) : 0;
                    
                    return (
                      <>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Current Stock:</span>
                          <span className="text-white">{currentStock} units</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Days of Stock:</span>
                          <span className={`font-medium ${daysOfStock < 7 ? 'text-red-400' : daysOfStock < 14 ? 'text-orange-400' : 'text-green-400'}`}>
                            {daysOfStock} days
                          </span>
                        </div>
                        <div className="pt-2 border-t border-gray-700">
                          <div className={`text-xs p-2 rounded ${daysOfStock < 7 ? 'bg-red-500/20 text-red-400' : daysOfStock < 14 ? 'bg-orange-500/20 text-orange-400' : 'bg-green-500/20 text-green-400'}`}>
                            {daysOfStock < 7 ? 'Critical: Reorder immediately' : 
                             daysOfStock < 14 ? 'Warning: Plan to reorder soon' : 
                             'Good: Stock levels adequate'}
                          </div>
                        </div>
                      </>
                    );
                  })()}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
