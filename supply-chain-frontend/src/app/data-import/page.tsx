'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { FileUpload } from '@/components/data-import/FileUpload';
import { dataImportAPI } from '@/lib/api';
import { Upload, Sparkles, Database, CheckCircle, AlertCircle, ArrowRight } from 'lucide-react';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

interface PreviewData {
  [key: string]: any;
}

interface UploadResult {
  success: boolean;
  message: string;
  upload_id: string;
  file_info: {
    filename: string;
    size: number;
    rows: number;
    columns: number;
    encoding: string;
  };
  preview_data: PreviewData[];
  column_mapping: Record<string, string>;
}

interface CleaningResult {
  success: boolean;
  message: string;
  upload_id: string;
  cleaned_data: PreviewData[];
  changes_summary: {
    total_rows: number;
    cleaned_fields: number;
    text_fields_processed: string[];
  };
}

interface ImportResult {
  success: boolean;
  message: string;
  imported_count: number;
  skipped_count: number;
  error_count: number;
  errors: string[];
}

export default function DataImportPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [cleaningResult, setCleaningResult] = useState<CleaningResult | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [currentStep, setCurrentStep] = useState<'upload' | 'preview' | 'clean' | 'import' | 'complete'>('upload');
  const [error, setError] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => dataImportAPI.uploadFile(file),
    onSuccess: (data: UploadResult) => {
      setUploadResult(data);
      setCurrentStep('preview');
      setError(null);
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Upload failed');
    },
  });

  const cleanMutation = useMutation({
    mutationFn: (uploadId: string) => dataImportAPI.cleanData(uploadId),
    onSuccess: (data: CleaningResult) => {
      setCleaningResult(data);
      setCurrentStep('import');
      setError(null);
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Data cleaning failed');
    },
  });

  const importMutation = useMutation({
    mutationFn: ({ uploadId, data }: { uploadId: string; data: PreviewData[] }) =>
      dataImportAPI.importData(uploadId, data, { skip_duplicates: true }),
    onSuccess: (data: ImportResult) => {
      setImportResult(data);
      setCurrentStep('complete');
      setError(null);
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Data import failed');
    },
  });

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
    setUploadResult(null);
    setCleaningResult(null);
    setImportResult(null);
    setCurrentStep('upload');
    setError(null);
  };

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  const handleCleanData = () => {
    if (uploadResult) {
      cleanMutation.mutate(uploadResult.upload_id);
    }
  };

  const handleImportData = () => {
    if (cleaningResult && uploadResult) {
      importMutation.mutate({
        uploadId: uploadResult.upload_id,
        data: cleaningResult.cleaned_data
      });
    }
  };

  const handleStartOver = () => {
    setSelectedFile(null);
    setUploadResult(null);
    setCleaningResult(null);
    setImportResult(null);
    setCurrentStep('upload');
    setError(null);
  };

  const renderPreviewTable = (data: PreviewData[], title: string) => (
    <div className="bg-[#1a1a1a] rounded-lg p-6">
      <h3 className="text-lg font-medium text-white mb-4">{title}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-600">
              {data.length > 0 && Object.keys(data[0]).map(key => (
                <th key={key} className="text-left py-2 px-3 text-gray-300 font-medium">
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 5).map((row, index) => (
              <tr key={index} className="border-b border-gray-700">
                {Object.values(row).map((value: any, valueIndex) => (
                  <td key={valueIndex} className="py-2 px-3 text-gray-400">
                    {String(value || '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {data.length > 5 && (
          <p className="text-gray-500 text-sm mt-2">
            Showing 5 of {data.length} rows
          </p>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-white mb-2">Data Import</h1>
        <p className="text-gray-400">
          Upload inventory data files with AI-powered cleaning and automatic record creation.
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center space-x-4 mb-8">
        <div className={`flex items-center space-x-2 ${currentStep !== 'upload' ? 'text-green-400' : 'text-orange-500'}`}>
          <Upload className="w-5 h-5" />
          <span className="text-sm font-medium">Upload</span>
        </div>
        <ArrowRight className="w-4 h-4 text-gray-500" />
        <div className={`flex items-center space-x-2 ${
          ['clean', 'import', 'complete'].includes(currentStep) ? 'text-green-400' : 
          currentStep === 'preview' ? 'text-orange-500' : 'text-gray-500'
        }`}>
          <Sparkles className="w-5 h-5" />
          <span className="text-sm font-medium">AI Clean</span>
        </div>
        <ArrowRight className="w-4 h-4 text-gray-500" />
        <div className={`flex items-center space-x-2 ${
          currentStep === 'complete' ? 'text-green-400' : 
          currentStep === 'import' ? 'text-orange-500' : 'text-gray-500'
        }`}>
          <Database className="w-5 h-5" />
          <span className="text-sm font-medium">Import</span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <span className="text-red-400">{error}</span>
        </div>
      )}

      {/* Step 1: File Upload */}
      {currentStep === 'upload' && (
        <div className="space-y-6">
          <FileUpload
            onFileSelect={handleFileSelect}
            onFileRemove={handleFileRemove}
            selectedFile={selectedFile}
            uploading={uploadMutation.isPending}
            error={error}
          />
          
          {selectedFile && !uploadMutation.isPending && (
            <div className="flex justify-center">
              <button
                onClick={handleUpload}
                className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
              >
                Upload & Preview Data
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Preview Data */}
      {currentStep === 'preview' && uploadResult && (
        <div className="space-y-6">
          <div className="bg-[#1a1a1a] rounded-lg p-6">
            <h2 className="text-xl font-medium text-white mb-4 flex items-center">
              <CheckCircle className="w-5 h-5 text-green-400 mr-2" />
              File Uploaded Successfully
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Filename:</span>
                <p className="text-white font-medium">{uploadResult.file_info.filename}</p>
              </div>
              <div>
                <span className="text-gray-400">Rows:</span>
                <p className="text-white font-medium">{uploadResult.file_info.rows}</p>
              </div>
              <div>
                <span className="text-gray-400">Columns:</span>
                <p className="text-white font-medium">{uploadResult.file_info.columns}</p>
              </div>
              <div>
                <span className="text-gray-400">Size:</span>
                <p className="text-white font-medium">{(uploadResult.file_info.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
          </div>

          {renderPreviewTable(uploadResult.preview_data, 'Data Preview')}

          <div className="flex justify-center space-x-4">
            <button
              onClick={handleStartOver}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Upload Different File
            </button>
            <button
              onClick={handleCleanData}
              disabled={cleanMutation.isPending}
              className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50 flex items-center space-x-2"
            >
              {cleanMutation.isPending && <LoadingSpinner />}
              <Sparkles className="w-4 h-4" />
              <span>Clean Data with AI</span>
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Import Data */}
      {currentStep === 'import' && cleaningResult && (
        <div className="space-y-6">
          <div className="bg-[#1a1a1a] rounded-lg p-6">
            <h2 className="text-xl font-medium text-white mb-4 flex items-center">
              <Sparkles className="w-5 h-5 text-orange-500 mr-2" />
              Data Cleaned Successfully
            </h2>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Total Rows:</span>
                <p className="text-white font-medium">{cleaningResult.changes_summary.total_rows}</p>
              </div>
              <div>
                <span className="text-gray-400">Fields Cleaned:</span>
                <p className="text-white font-medium">{cleaningResult.changes_summary.cleaned_fields}</p>
              </div>
              <div>
                <span className="text-gray-400">Text Fields Processed:</span>
                <p className="text-white font-medium">{cleaningResult.changes_summary.text_fields_processed.length}</p>
              </div>
            </div>
          </div>

          {renderPreviewTable(cleaningResult.cleaned_data, 'Cleaned Data Preview')}

          <div className="flex justify-center space-x-4">
            <button
              onClick={handleStartOver}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Start Over
            </button>
            <button
              onClick={handleImportData}
              disabled={importMutation.isPending}
              className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 flex items-center space-x-2"
            >
              {importMutation.isPending && <LoadingSpinner />}
              <Database className="w-4 h-4" />
              <span>Import to Inventory</span>
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Import Complete */}
      {currentStep === 'complete' && importResult && (
        <div className="space-y-6">
          <div className="bg-[#1a1a1a] rounded-lg p-6">
            <h2 className="text-xl font-medium text-white mb-4 flex items-center">
              <CheckCircle className="w-5 h-5 text-green-400 mr-2" />
              Import Completed Successfully
            </h2>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Imported:</span>
                <p className="text-green-400 font-bold text-lg">{importResult.imported_count}</p>
              </div>
              <div>
                <span className="text-gray-400">Skipped:</span>
                <p className="text-orange-400 font-bold text-lg">{importResult.skipped_count}</p>
              </div>
              <div>
                <span className="text-gray-400">Errors:</span>
                <p className="text-red-400 font-bold text-lg">{importResult.error_count}</p>
              </div>
            </div>
            
            {importResult.errors.length > 0 && (
              <div className="mt-4">
                <h4 className="text-white font-medium mb-2">Import Errors:</h4>
                <ul className="text-sm text-red-400 space-y-1">
                  {importResult.errors.slice(0, 5).map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                  {importResult.errors.length > 5 && (
                    <li className="text-gray-400">... and {importResult.errors.length - 5} more</li>
                  )}
                </ul>
              </div>
            )}
          </div>

          <div className="flex justify-center">
            <button
              onClick={handleStartOver}
              className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
            >
              Import More Data
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
