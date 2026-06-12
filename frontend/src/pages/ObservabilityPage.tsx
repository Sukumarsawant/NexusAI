import React, { useEffect, useState } from 'react';
import {
  Activity,
  Cpu,
  Clock,
  DollarSign,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell
} from 'recharts';
import { api } from '../services/api';
import { MetricsResponse, AgentPerformance, TraceItem } from '../types';

export const ObservabilityPage: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterAgent, setFilterAgent] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);

  const fetchObservability = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getMetrics();
      setMetrics(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch observability traces');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObservability();
  }, []);

  const filteredTraces = (metrics?.recent_traces || []).filter((t) => {
    if (filterAgent === 'all') return true;
    return t.agent_name.toLowerCase().includes(filterAgent.toLowerCase());
  });

  const agentChartData = (metrics?.agent_performance || []).map((ap) => ({
    name: ap.agent_name.replace(' Agent', ''),
    duration: ap.avg_duration_ms,
    tokens: ap.avg_tokens,
  }));

  const COLORS = ['#0c8ee9', '#6366f1', '#10b981', '#f59e0b', '#ec4899'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            LLM Multi-Agent Observability
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Fine-grained OpenTelemetry-compatible traces, token counts, latency breakdown, and agent metrics.
          </p>
        </div>
        <button
          onClick={fetchObservability}
          disabled={loading}
          className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 transition shadow-xs"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Traces</span>
        </button>
      </div>

      {/* Agent Performance Chart & Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-1">
            Agent Average Execution Duration (ms)
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
            Comparison of latency across individual multi-agent graph nodes.
          </p>
          <div className="h-64 w-full">
            {agentChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={agentChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
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
                  <Bar dataKey="duration" radius={[4, 4, 0, 0]}>
                    {agentChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No trace metrics captured yet.
              </div>
            )}
          </div>
        </div>

        {/* Overview Stats */}
        <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Telemetry Highlights
          </h2>
          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 flex justify-between items-center">
              <span className="text-slate-500">Total Recorded Traces</span>
              <span className="font-bold text-slate-900 dark:text-white">
                {metrics?.recent_traces.length ?? 0}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 flex justify-between items-center">
              <span className="text-slate-500">Total Cost (USD)</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                ${(metrics?.overview.total_cost_usd ?? 0).toFixed(4)}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 flex justify-between items-center">
              <span className="text-slate-500">Provider Token Tracking</span>
              <span className="font-bold text-brand-600 dark:text-brand-400 font-mono">
                {(metrics?.overview.total_tokens ?? 0).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Traces Table */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center space-x-2 font-semibold text-sm text-slate-900 dark:text-white">
            <Activity className="h-4 w-4 text-brand-500" />
            <span>Agent Execution Traces</span>
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={filterAgent}
              onChange={(e) => setFilterAgent(e.target.value)}
              className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none"
            >
              <option value="all">All Agents</option>
              <option value="query">Query Understanding</option>
              <option value="retrieval">Retrieval Agent</option>
              <option value="reasoning">Reasoning Agent</option>
              <option value="verification">Verification Agent</option>
              <option value="response">Response Agent</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 uppercase font-semibold border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-4 py-3">Agent</th>
                <th className="px-4 py-3">Order</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Input Tokens</th>
                <th className="px-4 py-3">Output Tokens</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Summary</th>
                <th className="px-4 py-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filteredTraces.length > 0 ? (
                filteredTraces.map((trace) => (
                  <tr key={trace.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/50 transition">
                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">
                      {trace.agent_name}
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono">#{trace.execution_order}</td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300 font-mono">
                      {trace.duration_ms} ms
                    </td>
                    <td className="px-4 py-3 text-slate-500 font-mono">{trace.input_tokens}</td>
                    <td className="px-4 py-3 text-slate-500 font-mono">{trace.output_tokens}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                        {trace.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300 max-w-xs truncate">
                      {trace.inputs_summary?.summary || '-'}
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono">
                      {new Date(trace.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                    No traces match your filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
