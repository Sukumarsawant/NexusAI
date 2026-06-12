import React, { useEffect, useState } from 'react';
import {
  Award,
  Play,
  CheckCircle2,
  Clock,
  AlertCircle,
  TrendingUp,
  FileText,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { api } from '../services/api';
import { EvaluationRunResponse } from '../types';

export const EvaluationPage: React.FC = () => {
  const [runs, setRuns] = useState<EvaluationRunResponse[]>([]);
  const [running, setRunning] = useState(false);
  const [selectedRun, setSelectedRun] = useState<EvaluationRunResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getEvaluationHistory();
      setRuns(data);
      if (data.length > 0 && !selectedRun) {
        setSelectedRun(data[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch evaluation history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleTriggerBenchmark = async () => {
    try {
      setRunning(true);
      setError(null);
      const newRun = await api.runEvaluation(`Enterprise QA Benchmark ${new Date().toLocaleTimeString()}`);
      await fetchRuns();
      setSelectedRun(newRun);
    } catch (err: any) {
      setError(err.message || 'Evaluation run failed');
    } finally {
      setRunning(false);
    }
  };

  const formatScore = (val?: number) => {
    if (val === undefined || val === null) return 'N/A';
    return `${(val * 100).toFixed(1)}%`;
  };

  const getScoreColor = (val?: number) => {
    if (val === undefined || val === null) return 'text-slate-400';
    if (val >= 0.85) return 'text-emerald-600 dark:text-emerald-400';
    if (val >= 0.70) return 'text-amber-600 dark:text-amber-400';
    return 'text-rose-600 dark:text-rose-400';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            RAGAS Evaluation Engine
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Standardized evaluation of Faithfulness, Answer Relevancy, Context Precision, and Context Recall.
          </p>
        </div>

        <button
          onClick={handleTriggerBenchmark}
          disabled={running}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition disabled:opacity-50"
        >
          <Play className={`h-4 w-4 ${running ? 'animate-spin' : ''}`} />
          <span>{running ? 'Running RAGAS Benchmark...' : 'Run Benchmark'}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 flex items-center space-x-3 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Latest Benchmark Scorecards */}
      {selectedRun && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
              Faithfulness
            </span>
            <div className={`mt-2 text-2xl font-bold ${getScoreColor(selectedRun.mean_faithfulness)}`}>
              {formatScore(selectedRun.mean_faithfulness)}
            </div>
            <p className="mt-1 text-xs text-slate-400">Grounding of claims in context</p>
          </div>

          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
              Answer Relevancy
            </span>
            <div className={`mt-2 text-2xl font-bold ${getScoreColor(selectedRun.mean_answer_relevancy)}`}>
              {formatScore(selectedRun.mean_answer_relevancy)}
            </div>
            <p className="mt-1 text-xs text-slate-400">Direct response to user question</p>
          </div>

          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
              Context Precision
            </span>
            <div className={`mt-2 text-2xl font-bold ${getScoreColor(selectedRun.mean_context_precision)}`}>
              {formatScore(selectedRun.mean_context_precision)}
            </div>
            <p className="mt-1 text-xs text-slate-400">Signal-to-noise ratio in retrieval</p>
          </div>

          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
              Context Recall
            </span>
            <div className={`mt-2 text-2xl font-bold ${getScoreColor(selectedRun.mean_context_recall)}`}>
              {formatScore(selectedRun.mean_context_recall)}
            </div>
            <p className="mt-1 text-xs text-slate-400">Coverage of ground truth facts</p>
          </div>
        </div>
      )}

      {/* Detailed Evaluation Questions Breakdown */}
      {selectedRun?.results && selectedRun.results.length > 0 && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 font-semibold text-sm text-slate-900 dark:text-white flex items-center justify-between">
            <span>Benchmark Questions & Answers ({selectedRun.results.length})</span>
            <span className="text-xs text-slate-400">Model: {selectedRun.model_name}</span>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {selectedRun.results.map((res) => (
              <div key={res.id} className="p-4 space-y-3">
                <div className="font-semibold text-sm text-slate-900 dark:text-white">
                  Q: {res.question}
                </div>
                {res.ground_truth && (
                  <div className="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/60 p-2.5 rounded-lg border border-slate-200/50 dark:border-slate-700">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">Ground Truth: </span>
                    {res.ground_truth}
                  </div>
                )}
                <div className="text-xs text-slate-700 dark:text-slate-300">
                  <span className="font-semibold">Generated Answer: </span>
                  {res.generated_answer}
                </div>
                <div className="flex flex-wrap gap-4 pt-1 text-xs font-mono">
                  <span>Faithfulness: <strong className={getScoreColor(res.faithfulness)}>{formatScore(res.faithfulness)}</strong></span>
                  <span>Relevancy: <strong className={getScoreColor(res.answer_relevancy)}>{formatScore(res.answer_relevancy)}</strong></span>
                  <span>Precision: <strong className={getScoreColor(res.context_precision)}>{formatScore(res.context_precision)}</strong></span>
                  <span>Recall: <strong className={getScoreColor(res.context_recall)}>{formatScore(res.context_recall)}</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Benchmark Runs History Table */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 font-semibold text-sm text-slate-900 dark:text-white">
          Historical Benchmark Runs ({runs.length})
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 uppercase font-semibold border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-4 py-3">Run Name</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Dataset Size</th>
                <th className="px-4 py-3">Faithfulness</th>
                <th className="px-4 py-3">Relevancy</th>
                <th className="px-4 py-3">Precision</th>
                <th className="px-4 py-3">Recall</th>
                <th className="px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {runs.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => setSelectedRun(r)}
                  className={`cursor-pointer transition ${
                    selectedRun?.id === r.id
                      ? 'bg-brand-50/70 dark:bg-brand-950/40'
                      : 'hover:bg-slate-50/50 dark:hover:bg-slate-850/50'
                  }`}
                >
                  <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">
                    {r.run_name}
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono">{r.dataset_size} QA pairs</td>
                  <td className={`px-4 py-3 font-mono ${getScoreColor(r.mean_faithfulness)}`}>
                    {formatScore(r.mean_faithfulness)}
                  </td>
                  <td className={`px-4 py-3 font-mono ${getScoreColor(r.mean_answer_relevancy)}`}>
                    {formatScore(r.mean_answer_relevancy)}
                  </td>
                  <td className={`px-4 py-3 font-mono ${getScoreColor(r.mean_context_precision)}`}>
                    {formatScore(r.mean_context_precision)}
                  </td>
                  <td className={`px-4 py-3 font-mono ${getScoreColor(r.mean_context_recall)}`}>
                    {formatScore(r.mean_context_recall)}
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                    No evaluations executed yet. Click "Run Benchmark" above to run RAGAS metrics.
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
