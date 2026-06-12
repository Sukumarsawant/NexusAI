import React from 'react';
import { CheckCircle2, Clock, Cpu, ArrowRight, ShieldCheck, Search, MessageSquare, Layers } from 'lucide-react';
import { AgentTraceItem } from '../types';

interface AgentTraceViewerProps {
  traces: AgentTraceItem[];
  totalDurationMs?: number;
}

export const AgentTraceViewer: React.FC<AgentTraceViewerProps> = ({ traces, totalDurationMs }) => {
  const getAgentIcon = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes('query')) return Search;
    if (n.includes('retrieval')) return Layers;
    if (n.includes('reasoning')) return Cpu;
    if (n.includes('verification')) return ShieldCheck;
    return MessageSquare;
  };

  return (
    <div className="mt-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-200 dark:border-slate-800">
        <span className="font-semibold text-slate-700 dark:text-slate-300 flex items-center space-x-1.5">
          <Cpu className="h-3.5 w-3.5 text-brand-500" />
          <span>Multi-Agent LangGraph Execution Flow</span>
        </span>
        {totalDurationMs !== undefined && (
          <span className="text-slate-500 dark:text-slate-400 font-mono">
            Total: {totalDurationMs} ms
          </span>
        )}
      </div>

      <div className="space-y-2">
        {traces.map((trace, idx) => {
          const Icon = getAgentIcon(trace.agent_name);
          return (
            <div
              key={idx}
              className="flex items-start justify-between p-2 rounded-lg bg-white dark:bg-slate-850 border border-slate-200/70 dark:border-slate-800 shadow-xs"
            >
              <div className="flex items-start space-x-2.5">
                <div className="p-1 rounded bg-slate-100 dark:bg-slate-800 text-brand-600 dark:text-brand-400 mt-0.5">
                  <Icon className="h-3.5 w-3.5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-slate-800 dark:text-slate-200">
                      {trace.agent_name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded-full font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                      {trace.status}
                    </span>
                  </div>
                  {trace.summary && (
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      {trace.summary}
                    </p>
                  )}
                </div>
              </div>

              <div className="text-right text-[11px] font-mono text-slate-500 dark:text-slate-400 shrink-0 ml-2">
                <div>{trace.duration_ms} ms</div>
                {(trace.input_tokens > 0 || trace.output_tokens > 0) && (
                  <div className="text-[10px] text-slate-400">
                    {trace.input_tokens + trace.output_tokens} tok
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
