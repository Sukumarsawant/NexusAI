import React, { useEffect, useState } from 'react';
import {
  FileText,
  CheckCircle,
  MessageSquare,
  Activity,
  Zap,
  DollarSign,
  TrendingUp,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { api } from '../services/api';
import { MetricOverview, LatencyTrendPoint } from '../types';
import { MetricCard } from '../components/MetricCard';

export const DashboardPage: React.FC = () => {
  const [overview, setOverview] = useState<MetricOverview | null>(null);
  const [latencyTrend, setLatencyTrend] = useState<LatencyTrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const metricsData = await api.getMetrics();
      setOverview(metricsData.overview);
      setLatencyTrend(metricsData.latency_trend || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load live metrics from backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Enterprise Intelligence Dashboard
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Real-time multi-agent execution pipeline telemetry and document ingestion state.
          </p>
        </div>
        <button
          onClick={fetchDashboardData}
          disabled={loading}
          className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-750 transition shadow-xs"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 flex items-center space-x-3 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Indexed Knowledge"
          value={overview?.indexed_documents ?? 0}
          subtext={`of ${overview?.total_documents ?? 0} total uploaded docs`}
          icon={FileText}
          variant="brand"
          badge="pgvector"
        />
        <MetricCard
          title="Total Conversations"
          value={overview?.total_conversations ?? 0}
          subtext="Multi-turn isolated sessions"
          icon={MessageSquare}
          variant="indigo"
        />
        <MetricCard
          title="Avg Pipeline Latency"
          value={`${overview?.avg_latency_ms ? (overview.avg_latency_ms / 1000).toFixed(2) : '0.00'}s`}
          subtext="End-to-end multi-agent execution"
          icon={Activity}
          variant="amber"
        />
        <MetricCard
          title="Estimated API Cost"
          value={`$${(overview?.total_cost_usd ?? 0).toFixed(4)}`}
          subtext={`Total tokens: ${(overview?.total_tokens ?? 0).toLocaleString()}`}
          icon={DollarSign}
          variant="emerald"
        />
      </div>

      {/* Latency and Token Ingestion Chart */}
      <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              End-to-End Request Latency Trend
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Live multi-agent graph turn response duration (ms)
            </p>
          </div>
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-brand-500"></span>
            <span>Latency (ms)</span>
          </div>
        </div>

        <div className="h-72 w-full">
          {latencyTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={latencyTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0c8ee9" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#0c8ee9" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                <XAxis dataKey="timestamp" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#1e293b',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '12px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="latency_ms"
                  stroke="#0c8ee9"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#latencyGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400 text-sm">
              No recent requests yet. Run queries in AI Chat to generate live telemetry.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
