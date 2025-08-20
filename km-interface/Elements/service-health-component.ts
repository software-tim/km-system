import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, AlertTriangle, XCircle, RefreshCw } from 'lucide-react';

interface ServiceStatus {
  title: string;
  status: 'healthy' | 'degraded' | 'down';
  responseTime: string;
  icon: string;
  url: string;
  description: string;
}

interface HealthResponse {
  summary: {
    healthy: number;
    total: number;
  };
  services: ServiceStatus[];
}

const ServiceHealth: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchHealthData = async () => {
    try {
      const response = await fetch('https://km-orchestrator.azurewebsites.net/api/simple-test');
      const data: HealthResponse = await response.json();
      setHealthData(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch health data:', error);
      // Set error state
      setHealthData({
        summary: { healthy: 0, total: 4 },
        services: [
          {
            title: 'Connection Error',
            status: 'down',
            responseTime: 'N/A',
            icon: '❌',
            url: '',
            description: 'Unable to connect to orchestrator'
          }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    // Update every 30 seconds
    const interval = setInterval(fetchHealthData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'down':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Activity className="w-5 h-5 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'border-green-500 bg-green-500/10';
      case 'degraded':
        return 'border-yellow-500 bg-yellow-500/10';
      case 'down':
        return 'border-red-500 bg-red-500/10';
      default:
        return 'border-slate-600 bg-slate-800';
    }
  };

  const getResponseTimeColor = (responseTime: string) => {
    const time = parseInt(responseTime);
    if (time < 200) return 'text-green-400';
    if (time < 500) return 'text-yellow-400';
    return 'text-red-400';
  };

  const overallHealth = healthData 
    ? (healthData.summary.healthy / healthData.summary.total) * 100 
    : 0;

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-20 bg-slate-800 rounded-lg"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-slate-800 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Overall Health Summary */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-600">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium text-white">System Health</h3>
          <button
            onClick={fetchHealthData}
            className="p-1 text-slate-400 hover:text-white transition-colors"
            title="Refresh status"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex-1">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-300">Overall Health</span>
              <span className="text-slate-300">{overallHealth.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  overallHealth >= 80 ? 'bg-green-500' :
                  overallHealth >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${overallHealth}%` }}
              ></div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-white">
              {healthData?.summary.healthy || 0}/{healthData?.summary.total || 0}
            </div>
            <div className="text-xs text-slate-400">Services Online</div>
          </div>
        </div>
        
        <div className="text-xs text-slate-400 mt-2">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </div>
      </div>

      {/* Individual Service Status */}
      <div className="space-y-3">
        {healthData?.services.map((service, index) => (
          <div
            key={index}
            className={`rounded-lg p-4 border transition-all duration-200 ${getStatusColor(service.status)}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-xl">{service.icon}</span>
                <div>
                  <h4 className="font-medium text-white">{service.title}</h4>
                  <p className="text-xs text-slate-400">{service.description}</p>
                </div>
              </div>
              
              <div className="text-right space-y-1">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(service.status)}
                  <span className="text-sm font-medium text-white capitalize">
                    {service.status}
                  </span>
                </div>
                <div className={`text-xs font-mono ${getResponseTimeColor(service.responseTime)}`}>
                  {service.responseTime}
                </div>
              </div>
            </div>
            
            {/* Service Details */}
            {service.status === 'healthy' && (
              <div className="mt-2 pt-2 border-t border-slate-700">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Status: Operational</span>
                  <span>Uptime: 99.9%</span>
                </div>
              </div>
            )}
            
            {service.status === 'degraded' && (
              <div className="mt-2 pt-2 border-t border-yellow-500/20">
                <div className="text-xs text-yellow-300 bg-yellow-500/10 rounded p-2">
                  ⚠️ Experiencing slower than normal response times
                </div>
              </div>
            )}
            
            {service.status === 'down' && (
              <div className="mt-2 pt-2 border-t border-red-500/20">
                <div className="text-xs text-red-300 bg-red-500/10 rounded p-2">
                  🚨 Service unavailable - investigating issue
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Service Dependencies */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-600">
        <h4 className="font-medium text-white mb-3">Service Dependencies</h4>
        <div className="text-sm text-slate-300 space-y-2">
          <div className="flex justify-between">
            <span>Document Storage</span>
            <span className="text-green-400">✓ Connected</span>
          </div>
          <div className="flex justify-between">
            <span>Search Engine</span>
            <span className="text-green-400">✓ Connected</span>
          </div>
          <div className="flex justify-between">
            <span>AI Processing</span>
            <span className="text-green-400">✓ Connected</span>
          </div>
          <div className="flex justify-between">
            <span>Graph Database</span>
            <span className="text-green-400">✓ Connected</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-600">
        <h4 className="font-medium text-white mb-3">Quick Actions</h4>
        <div className="grid grid-cols-2 gap-2">
          <button className="text-xs bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded transition-colors">
            View Logs
          </button>
          <button className="text-xs bg-slate-700 hover:bg-slate-600 text-white py-2 px-3 rounded transition-colors">
            Run Diagnostics
          </button>
          <button className="text-xs bg-slate-700 hover:bg-slate-600 text-white py-2 px-3 rounded transition-colors">
            Performance
          </button>
          <button className="text-xs bg-slate-700 hover:bg-slate-600 text-white py-2 px-3 rounded transition-colors">
            Settings
          </button>
        </div>
      </div>
    </div>
  );
};

export default ServiceHealth;