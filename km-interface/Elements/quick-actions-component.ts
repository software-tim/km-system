import React, { useState } from 'react';
import { Upload, Search, FileText, MessageSquare, Settings, BarChart3, Download, RefreshCw } from 'lucide-react';

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
  category: 'primary' | 'secondary';
  disabled?: boolean;
}

const QuickActions: React.FC = () => {
  const [uploadModal, setUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileUpload = async () => {
    if (!uploadFile) return;

    setUploading(true);
    try {
      // Convert file to text for document upload
      const text = await uploadFile.text();
      const response = await fetch('https://km-orchestrator.azurewebsites.net/tools/store-document', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: uploadFile.name,
          content: text,
          classification: 'User Upload',
          entities: 'document, upload',
          file_type: uploadFile.name.split('.').pop() || 'txt'
        })
      });

      if (response.ok) {
        alert('Document uploaded successfully!');
        setUploadModal(false);
        setUploadFile(null);
      } else {
        alert('Upload failed. Please try again.');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const quickActions: QuickAction[] = [
    {
      id: 'upload',
      title: 'Upload Document',
      description: 'Add new documents to knowledge base',
      icon: <Upload className="w-5 h-5" />,
      action: () => setUploadModal(true),
      category: 'primary'
    },
    {
      id: 'search',
      title: 'Advanced Search',
      description: 'Search across all documents',
      icon: <Search className="w-5 h-5" />,
      action: () => window.location.href = '/search',
      category: 'primary'
    },
    {
      id: 'chat',
      title: 'AI Assistant',
      description: 'Ask questions about your data',
      icon: <MessageSquare className="w-5 h-5" />,
      action: () => window.location.href = '/chat',
      category: 'primary'
    },
    {
      id: 'analytics',
      title: 'Analytics',
      description: 'View usage and insights',
      icon: <BarChart3 className="w-5 h-5" />,
      action: () => window.location.href = '/analytics',
      category: 'secondary'
    },
    {
      id: 'export',
      title: 'Export Data',
      description: 'Download your documents',
      icon: <Download className="w-5 h-5" />,
      action: () => alert('Export feature coming soon!'),
      category: 'secondary',
      disabled: true
    },
    {
      id: 'settings',
      title: 'Settings',
      description: 'Configure your workspace',
      icon: <Settings className="w-5 h-5" />,
      action: () => window.location.href = '/settings',
      category: 'secondary'
    }
  ];

  const primaryActions = quickActions.filter(action => action.category === 'primary');
  const secondaryActions = quickActions.filter(action => action.category === 'secondary');

  return (
    <div className="space-y-6">
      {/* Primary Actions - Large Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {primaryActions.map((action) => (
          <button
            key={action.id}
            onClick={action.action}
            disabled={action.disabled}
            className="group relative bg-gradient-to-br from-slate-800 to-slate-700 hover:from-slate-700 hover:to-slate-600 disabled:from-slate-800 disabled:to-slate-800 border border-slate-600 hover:border-slate-500 rounded-lg p-6 text-left transition-all duration-200 hover:scale-105 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <div className="flex items-center space-x-3 mb-3">
              <div className="p-2 bg-blue-600/20 rounded-lg text-blue-400 group-hover:bg-blue-600/30 transition-colors">
                {action.icon}
              </div>
              <h3 className="font-semibold text-white">{action.title}</h3>
            </div>
            <p className="text-sm text-slate-400 group-hover:text-slate-300 transition-colors">
              {action.description}
            </p>
            
            {/* Hover effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 to-purple-600/5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>
        ))}
      </div>

      {/* Secondary Actions - Compact Grid */}
      <div>
        <h3 className="text-sm font-medium text-slate-300 mb-3">More Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {secondaryActions.map((action) => (
            <button
              key={action.id}
              onClick={action.action}
              disabled={action.disabled}
              className="flex items-center space-x-3 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-800 border border-slate-600 hover:border-slate-500 rounded-lg p-4 transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <div className="text-slate-400">
                {action.icon}
              </div>
              <div className="text-left flex-1">
                <h4 className="text-sm font-medium text-white">{action.title}</h4>
                <p className="text-xs text-slate-400">{action.description}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-600">
        <h3 className="text-sm font-medium text-slate-300 mb-3">Quick Stats</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-lg font-bold text-blue-400">1,247</div>
            <div className="text-xs text-slate-400">Documents</div>
          </div>
          <div>
            <div className="text-lg font-bold text-green-400">89</div>
            <div className="text-xs text-slate-400">Searches Today</div>
          </div>
          <div>
            <div className="text-lg font-bold text-purple-400">23</div>
            <div className="text-xs text-slate-400">Uploads This Week</div>
          </div>
          <div>
            <div className="text-lg font-bold text-cyan-400">145ms</div>
            <div className="text-xs text-slate-400">Avg Response</div>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {uploadModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4 border border-slate-600">
            <h2 className="text-xl font-semibold text-white mb-4">Upload Document</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Select File
                </label>
                <input
                  type="file"
                  accept=".txt,.md,.pdf,.doc,.docx"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Supported: .txt, .md, .pdf, .doc, .docx
                </p>
              </div>

              {uploadFile && (
                <div className="bg-slate-700 rounded-lg p-3">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-5 h-5 text-blue-400" />
                    <div>
                      <p className="text-sm font-medium text-white">{uploadFile.name}</p>
                      <p className="text-xs text-slate-400">
                        {(uploadFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setUploadModal(false);
                    setUploadFile(null);
                  }}
                  className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2 px-4 rounded-lg transition-colors"
                  disabled={uploading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleFileUpload}
                  disabled={!uploadFile || uploading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      <span>Upload</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuickActions;