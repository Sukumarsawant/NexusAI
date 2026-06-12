import React, { useEffect, useState, useRef } from 'react';
import {
  Upload,
  FileText,
  Trash2,
  RefreshCw,
  Search,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  Database,
  Sliders
} from 'lucide-react';
import { api } from '../services/api';
import { DocumentItem, SearchResponse } from '../types';

export const KnowledgeBasePage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chunkSize, setChunkSize] = useState(800);
  const [chunkOverlap, setChunkOverlap] = useState(150);
  const [showConfig, setShowConfig] = useState(false);

  // Search Tester state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [searching, setSearching] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const docs = await api.listDocuments();
      setDocuments(docs);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      await api.uploadDocument(file, chunkSize, chunkOverlap);
      await fetchDocuments();
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err: any) {
      setError(err.message || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document and all its indexed chunks?')) return;
    try {
      await api.deleteDocument(id);
      setDocuments(documents.filter((d) => d.id !== id));
    } catch (err: any) {
      alert(`Delete error: ${err.message}`);
    }
  };

  const handleReindex = async (id: string) => {
    try {
      await api.reindexDocument(id);
      await fetchDocuments();
    } catch (err: any) {
      alert(`Re-index error: ${err.message}`);
    }
  };

  const handleSearchProbe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setSearching(true);
      const res = await api.search(searchQuery, 'hybrid', 5, 0.5);
      setSearchResults(res);
    } catch (err: any) {
      alert(`Search error: ${err.message}`);
    } finally {
      setSearching(false);
    }
  };

  const getStatusBadge = (status: DocumentItem['status'], errorMsg?: string) => {
    switch (status) {
      case 'indexed':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle2 className="h-3 w-3" />
            <span>Indexed</span>
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300 border border-brand-200 dark:border-brand-800">
            <Clock className="h-3 w-3 animate-spin" />
            <span>Processing</span>
          </span>
        );
      case 'failed':
        return (
          <span
            className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800 cursor-help"
            title={errorMsg || 'Ingestion failed'}
          >
            <XCircle className="h-3 w-3" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <span>Pending</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Upload Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Enterprise Knowledge Base
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Upload enterprise documents (PDF, TXT, Markdown, CSV) with semantic chunking & pgvector indexing.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 transition"
            title="Configure chunk size & overlap"
          >
            <Sliders className="h-4 w-4" />
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md,.csv"
            onChange={handleFileUpload}
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition disabled:opacity-50"
          >
            <Upload className={`h-4 w-4 ${uploading ? 'animate-bounce' : ''}`} />
            <span>{uploading ? 'Ingesting Document...' : 'Upload Document'}</span>
          </button>
        </div>
      </div>

      {/* Config Drawer */}
      {showConfig && (
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="font-medium text-slate-700 dark:text-slate-300 block mb-1">
              Chunk Size (characters): {chunkSize}
            </label>
            <input
              type="range"
              min={200}
              max={2000}
              step={50}
              value={chunkSize}
              onChange={(e) => setChunkSize(Number(e.target.value))}
              className="w-full accent-brand-500"
            />
          </div>
          <div>
            <label className="font-medium text-slate-700 dark:text-slate-300 block mb-1">
              Chunk Overlap (characters): {chunkOverlap}
            </label>
            <input
              type="range"
              min={20}
              max={400}
              step={10}
              value={chunkOverlap}
              onChange={(e) => setChunkOverlap(Number(e.target.value))}
              className="w-full accent-brand-500"
            />
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 flex items-center space-x-3 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Document Table */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2 font-semibold text-sm text-slate-900 dark:text-white">
            <Database className="h-4 w-4 text-brand-500" />
            <span>Ingested Documents ({documents.length})</span>
          </div>
          <button
            onClick={fetchDocuments}
            className="text-xs text-slate-500 hover:text-slate-900 dark:hover:text-white inline-flex items-center space-x-1"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Refresh</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 uppercase font-semibold border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-4 py-3">Document</th>
                <th className="px-4 py-3">Format</th>
                <th className="px-4 py-3">Size</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Chunks</th>
                <th className="px-4 py-3">Uploaded</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {documents.length > 0 ? (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/50 transition">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white flex items-center space-x-2">
                      <FileText className="h-4 w-4 text-brand-500 shrink-0" />
                      <span className="truncate max-w-xs">{doc.filename}</span>
                    </td>
                    <td className="px-4 py-3 uppercase text-slate-500">{doc.file_type}</td>
                    <td className="px-4 py-3 text-slate-500 font-mono">
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td className="px-4 py-3">{getStatusBadge(doc.status, doc.error_message)}</td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300 font-semibold font-mono">
                      {doc.chunk_count}
                    </td>
                    <td className="px-4 py-3 text-slate-400">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <button
                        onClick={() => handleReindex(doc.id)}
                        title="Re-index document"
                        className="p-1 rounded text-slate-400 hover:text-brand-600 transition"
                      >
                        <RefreshCw className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        title="Delete document"
                        className="p-1 rounded text-slate-400 hover:text-rose-600 transition"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                    No documents uploaded yet. Upload your first PDF, TXT, Markdown, or CSV file above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Retrieval Probe Tester */}
      <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Hybrid Retrieval Engine Inspector
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Probe pgvector vector similarity and keyword full-text matching with Reciprocal Rank Fusion (RRF).
          </p>
        </div>

        <form onSubmit={handleSearchProbe} className="flex gap-2">
          <input
            type="text"
            placeholder="Test search across your knowledge base..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3.5 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <button
            type="submit"
            disabled={searching}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 hover:opacity-90 transition disabled:opacity-50"
          >
            {searching ? 'Retrieving...' : 'Search Engine'}
          </button>
        </form>

        {searchResults && (
          <div className="mt-4 space-y-2">
            <div className="text-xs text-slate-500 flex justify-between">
              <span>Returned {searchResults.total_results} chunks ({searchResults.strategy})</span>
              <span>Execution: {searchResults.search_duration_ms} ms</span>
            </div>
            <div className="space-y-2">
              {searchResults.results.map((r, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between font-medium text-slate-800 dark:text-slate-200">
                    <span>
                      {r.filename} {r.page_or_row ? `(${r.page_or_row})` : ''} - Chunk #{r.chunk_index}
                    </span>
                    <span className="font-mono text-brand-600 dark:text-brand-400">
                      Score: {(r.similarity_score * 100).toFixed(1)}% ({r.retrieval_method})
                    </span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-400">{r.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
