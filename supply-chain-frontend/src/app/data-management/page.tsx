'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dataManagementAPI } from '@/lib/api';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { Upload, Download, RefreshCw, AlertTriangle } from 'lucide-react';

const tabs = ['Details', 'Clean Data', 'View Errors', 'Importing Data'];

function StatusBadge({ status }: { status: string }) {
  if (status === 'completed') {
    return <span className="status-completed">Completed</span>;
  }
  return <span className="status-in-progress">In Progress</span>;
}

function QualityScore({ score }: { score: number }) {
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-32 h-32 mx-auto">
      <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="45"
          stroke="#374151"
          strokeWidth="8"
          fill="none"
        />
        <circle
          cx="50"
          cy="50"
          r="45"
          stroke="#f59e0b"
          strokeWidth="8"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold text-white">{score}%</div>
          <div className="text-xs text-gray-400">Quality Score</div>
        </div>
      </div>
    </div>
  );
}

export default function DataManagement() {
  const [activeTab, setActiveTab] = useState('Details');
  const queryClient = useQueryClient();

  // Fetch data management overview
  const { data: overview, isLoading, error, refetch } = useQuery({
    queryKey: ['data-management-overview'],
    queryFn: dataManagementAPI.getOverview,
  });

  // Import data mutation
  const importDataMutation = useMutation({
    mutationFn: ({ fileType, source }: { fileType: string; source: string }) =>
      dataManagementAPI.importData(fileType, source),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-management-overview'] });
    },
  });

  // Clean data mutation
  const cleanDataMutation = useMutation({
    mutationFn: dataManagementAPI.cleanData,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-management-overview'] });
    },
  });

  if (isLoading) {
    return <LoadingSpinner message="Loading data management..." />;
  }

  if (error) {
    return <ErrorMessage message="Failed to load data management overview" onRetry={() => refetch()} />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-white">Data Management</h1>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-gray-300 hover:text-white flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={() => importDataMutation.mutate({ fileType: 'csv', source: 'manual' })}
            disabled={importDataMutation.isPending}
            className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 flex items-center disabled:opacity-50"
          >
            <Upload className="w-4 h-4 mr-2" />
            {importDataMutation.isPending ? 'Importing...' : 'Import Data'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-orange-500 text-orange-500'
                  : 'border-transparent text-gray-300 hover:text-white hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'Details' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Data Overview */}
          <div className="lg:col-span-2">
            <div className="space-y-6">
              {/* Data Overview Cards */}
              <div>
                <h2 className="text-lg font-medium text-white mb-4">Data Overview</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-[#1a1a1a] p-6 rounded-lg">
                    <h3 className="text-sm text-gray-400 mb-2">Total Records</h3>
                    <p className="text-2xl font-bold text-white">{overview?.total_records?.toLocaleString()}</p>
                  </div>
                  <div className="bg-[#1a1a1a] p-6 rounded-lg">
                    <h3 className="text-sm text-gray-400 mb-2">Clean Records</h3>
                    <p className="text-2xl font-bold text-white">{overview?.clean_records?.toLocaleString()}</p>
                  </div>
                  <div className="bg-[#1a1a1a] p-6 rounded-lg">
                    <h3 className="text-sm text-gray-400 mb-2">Error Records</h3>
                    <p className="text-2xl font-bold text-white text-red-400">{overview?.error_records?.toLocaleString()}</p>
                  </div>
                  <div className="bg-[#1a1a1a] p-6 rounded-lg">
                    <h3 className="text-sm text-gray-400 mb-2">Last Updated</h3>
                    <p className="text-lg font-bold text-white">
                      {overview?.last_updated ? new Date(overview.last_updated).toLocaleString() : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Recent Activities */}
              <div>
                <h2 className="text-lg font-medium text-white mb-4">Recent Activities</h2>
                <div className="bg-[#1a1a1a] rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-700">
                        <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                          Activity
                        </th>
                        <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                          Timestamp
                        </th>
                        <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="text-left py-4 px-6 text-sm font-medium text-gray-400 uppercase tracking-wider">
                          Details
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {overview?.recent_activities?.map((activity, index) => (
                        <tr 
                          key={index} 
                          className={`border-b border-gray-700 hover:bg-gray-800/50 ${
                            index % 2 === 0 ? 'bg-[#111111]' : 'bg-[#1a1a1a]'
                          }`}
                        >
                          <td className="py-4 px-6 text-white">
                            {activity.activity}
                          </td>
                          <td className="py-4 px-6 text-gray-300">
                            {new Date(activity.timestamp).toLocaleString()}
                          </td>
                          <td className="py-4 px-6">
                            <StatusBadge status={activity.status} />
                          </td>
                          <td className="py-4 px-6 text-gray-400 text-sm">
                            {activity.records_processed && `${activity.records_processed} records`}
                            {activity.errors_fixed && `${activity.errors_fixed} errors fixed`}
                            {activity.errors_remaining && `${activity.errors_remaining} remaining`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Data Quality */}
          <div>
            <div className="bg-[#1a1a1a] p-6 rounded-lg">
              <h2 className="text-lg font-medium text-white mb-6">Data Quality</h2>
              <QualityScore score={overview?.data_quality_score || 95} />
            </div>
          </div>
        </div>
      )}

      {/* Clean Data Tab */}
      {activeTab === 'Clean Data' && (
        <div className="space-y-6">
          <div className="bg-[#1a1a1a] p-6 rounded-lg">
            <h2 className="text-lg font-medium text-white mb-4">Data Cleaning Operations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-md font-medium text-gray-300">Available Operations</h3>
                <button
                  onClick={() => cleanDataMutation.mutate()}
                  disabled={cleanDataMutation.isPending}
                  className="w-full px-4 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 flex items-center justify-center"
                >
                  {cleanDataMutation.isPending ? (
                    <>Processing...</>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Clean Data Now
                    </>
                  )}
                </button>
                <div className="text-sm text-gray-400">
                  This will remove duplicates, fix formatting issues, and validate data integrity.
                </div>
              </div>
              <div className="space-y-4">
                <h3 className="text-md font-medium text-gray-300">Last Cleaning Results</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Records Cleaned:</span>
                    <span className="text-white">156</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Errors Fixed:</span>
                    <span className="text-green-400">23</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Duplicates Removed:</span>
                    <span className="text-yellow-400">8</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Importing Data Tab */}
      {activeTab === 'Importing Data' && (
        <div className="space-y-6">
          <div className="bg-[#1a1a1a] p-6 rounded-lg">
            <h2 className="text-lg font-medium text-white mb-4">Data Import</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => importDataMutation.mutate({ fileType: 'csv', source: 'file' })}
                disabled={importDataMutation.isPending}
                className="p-6 border-2 border-dashed border-gray-600 rounded-lg hover:border-orange-500 hover:bg-orange-500/10 transition-colors disabled:opacity-50"
              >
                <Upload className="w-8 h-8 text-gray-400 mb-2 mx-auto" />
                <div className="text-white font-medium">CSV Import</div>
                <div className="text-gray-400 text-sm">Upload CSV files</div>
              </button>
              <button
                onClick={() => importDataMutation.mutate({ fileType: 'json', source: 'api' })}
                disabled={importDataMutation.isPending}
                className="p-6 border-2 border-dashed border-gray-600 rounded-lg hover:border-orange-500 hover:bg-orange-500/10 transition-colors disabled:opacity-50"
              >
                <Download className="w-8 h-8 text-gray-400 mb-2 mx-auto" />
                <div className="text-white font-medium">API Import</div>
                <div className="text-gray-400 text-sm">From external APIs</div>
              </button>
              <button
                onClick={() => importDataMutation.mutate({ fileType: 'xlsx', source: 'manual' })}
                disabled={importDataMutation.isPending}
                className="p-6 border-2 border-dashed border-gray-600 rounded-lg hover:border-orange-500 hover:bg-orange-500/10 transition-colors disabled:opacity-50"
              >
                <Upload className="w-8 h-8 text-gray-400 mb-2 mx-auto" />
                <div className="text-white font-medium">Excel Import</div>
                <div className="text-gray-400 text-sm">Upload XLSX files</div>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Errors Tab */}
      {activeTab === 'View Errors' && (
        <div className="space-y-6">
          <div className="bg-[#1a1a1a] p-6 rounded-lg">
            <div className="flex items-center mb-4">
              <AlertTriangle className="w-6 h-6 text-red-400 mr-2" />
              <h2 className="text-lg font-medium text-white">Data Errors</h2>
            </div>
            <div className="text-center py-8">
              <div className="text-6xl text-red-400 mb-4">{overview?.error_records || 0}</div>
              <div className="text-white font-medium mb-2">Error Records Found</div>
              <div className="text-gray-400">These records require manual review and correction</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
