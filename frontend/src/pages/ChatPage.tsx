import React, { useEffect, useState, useRef } from 'react';
import {
  Send,
  Plus,
  Trash2,
  Bot,
  User as UserIcon,
  Cpu,
  ShieldCheck,
  AlertCircle,
  FileText,
  Clock,
  Sparkles,
  Layers,
  Search
} from 'lucide-react';
import { api } from '../services/api';
import { ConversationItem, MessageItem, ChatResponse, AgentTraceItem } from '../types';
import { CitationBadge } from '../components/CitationBadge';
import { AgentTraceViewer } from '../components/AgentTraceViewer';

export const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [executingAgent, setExecutingAgent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
      if (convs.length > 0 && !activeConvId) {
        selectConversation(convs[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load conversations', err);
    }
  };

  const selectConversation = async (convId: string) => {
    setActiveConvId(convId);
    try {
      const conv = await api.getConversation(convId);
      setMessages(conv.messages || []);
      setTimeout(scrollToBottom, 100);
    } catch (err: any) {
      setError(err.message || 'Failed to load conversation messages');
    }
  };

  const startNewConversation = () => {
    setActiveConvId(null);
    setMessages([]);
  };

  const deleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this conversation?')) return;
    try {
      await api.deleteConversation(convId);
      setConversations(conversations.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        startNewConversation();
      }
    } catch (err: any) {
      alert(`Delete error: ${err.message}`);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = inputQuery.trim();
    if (!query || loading) return;

    setInputQuery('');
    setError(null);
    setLoading(true);

    // Optimistically append user message
    const tempUserMsg: MessageItem = {
      id: `temp-${Date.now()}`,
      conversation_id: activeConvId || '',
      role: 'user',
      content: query,
      citations: [],
      retrieved_context: [],
      agent_trace_summary: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setTimeout(scrollToBottom, 50);

    // Simulated step indicators for visual feedback while backend graph runs
    setExecutingAgent('Query Understanding Agent (Analyzing intent & entities)...');
    const t1 = setTimeout(() => {
      setExecutingAgent('Retrieval Agent (Performing hybrid pgvector & keyword search)...');
    }, 800);
    const t2 = setTimeout(() => {
      setExecutingAgent('Reasoning Agent (Synthesizing evidence across documents)...');
    }, 1800);
    const t3 = setTimeout(() => {
      setExecutingAgent('Verification Agent (Auditing grounded claims & citations)...');
    }, 2800);

    try {
      const response: ChatResponse = await api.sendChat(query, activeConvId || undefined);

      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      setExecutingAgent(null);

      // Assistant message
      const asstMsg: MessageItem = {
        id: response.message_id,
        conversation_id: response.conversation_id,
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        retrieved_context: response.retrieved_contexts,
        agent_trace_summary: {
          traces: response.agent_traces,
          duration_ms: response.total_duration_ms,
        },
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, asstMsg]);
      setActiveConvId(response.conversation_id);
      loadConversations();
      setTimeout(scrollToBottom, 100);
    } catch (err: any) {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      setExecutingAgent(null);
      setError(err.message || 'Execution error during multi-agent graph turn');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
      {/* Conversation Sidebar */}
      <div className="w-72 border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 flex flex-col justify-between shrink-0">
        <div className="p-3 border-b border-slate-200 dark:border-slate-800">
          <button
            onClick={startNewConversation}
            className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-lg text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-xs transition"
          >
            <Plus className="h-4 w-4" />
            <span>New Session</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => selectConversation(conv.id)}
              className={`group flex items-center justify-between p-2.5 rounded-lg text-xs cursor-pointer transition ${
                activeConvId === conv.id
                  ? 'bg-white dark:bg-slate-800 text-brand-600 dark:text-brand-400 font-semibold shadow-xs border border-slate-200/80 dark:border-slate-700'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-white/60 dark:hover:bg-slate-800/60'
              }`}
            >
              <span className="truncate flex-1">{conv.title || 'Untitled Session'}</span>
              <button
                onClick={(e) => deleteConversation(conv.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-500 transition ml-1"
                title="Delete"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          ))}
          {conversations.length === 0 && (
            <div className="p-4 text-center text-slate-400 text-xs">No active sessions</div>
          )}
        </div>

        <div className="p-3 border-t border-slate-200 dark:border-slate-800 text-[11px] text-slate-400 text-center">
          Persisted via PostgreSQL
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col justify-between overflow-hidden bg-white dark:bg-slate-900">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-3">
              <div className="h-12 w-12 rounded-xl bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 flex items-center justify-center border border-brand-200/50">
                <Sparkles className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-slate-900 dark:text-white">
                Enterprise Multi-Agent Intelligence
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Ask analytical questions across your ingested enterprise data.
                Our multi-agent pipeline coordinates query expansion, hybrid retrieval, synthesis,
                and hallucination verification.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 text-sm ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.role === 'assistant' && (
                <div className="h-8 w-8 rounded-lg bg-brand-600 text-white flex items-center justify-center shrink-0 shadow-xs mt-1">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-2xl px-4 py-3 leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-brand-600 text-white shadow-xs rounded-tr-none'
                    : 'bg-slate-50 dark:bg-slate-850 text-slate-900 dark:text-slate-100 border border-slate-200/70 dark:border-slate-800 rounded-tl-none shadow-xs'
                }`}
              >
                {/* Content */}
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Citations if available */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-slate-200 dark:border-slate-700/80">
                    <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1 flex items-center space-x-1">
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
                      <span>Verified Citations ({msg.citations.length})</span>
                    </div>
                    <div className="flex flex-wrap">
                      {msg.citations.map((c, idx) => (
                        <CitationBadge key={idx} citation={c} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Multi-Agent Trace Drawer */}
                {msg.agent_trace_summary?.traces && msg.agent_trace_summary.traces.length > 0 && (
                  <AgentTraceViewer
                    traces={msg.agent_trace_summary.traces}
                    totalDurationMs={msg.agent_trace_summary.duration_ms}
                  />
                )}
              </div>

              {msg.role === 'user' && (
                <div className="h-8 w-8 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center shrink-0 mt-1">
                  <UserIcon className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}

          {/* Active Agent Status Indicator */}
          {loading && (
            <div className="flex items-start space-x-3 text-sm">
              <div className="h-8 w-8 rounded-lg bg-brand-600 text-white flex items-center justify-center shrink-0 animate-pulse mt-1">
                <Bot className="h-4 w-4" />
              </div>
              <div className="p-3.5 rounded-2xl rounded-tl-none bg-slate-50 dark:bg-slate-850 border border-slate-200/70 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300 flex items-center space-x-2.5 shadow-xs">
                <Clock className="h-4 w-4 text-brand-500 animate-spin" />
                <span className="font-mono">{executingAgent || 'Agents Coordinating...'}</span>
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Query Input Box */}
        <form
          onSubmit={handleSendMessage}
          className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center space-x-3"
        >
          <input
            type="text"
            placeholder="Ask a question across your enterprise documents..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={loading}
            className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
          />
          <button
            type="submit"
            disabled={loading || !inputQuery.trim()}
            className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
