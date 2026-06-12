export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  content_hash: string;
  status: 'pending' | 'processing' | 'indexed' | 'failed';
  chunk_count: number;
  error_message?: string;
  doc_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CitationItem {
  source_id: string;
  filename: string;
  chunk_index: number;
  page_or_row?: string;
  snippet: string;
  relevance_score: number;
}

export interface AgentTraceItem {
  agent_name: string;
  execution_order: number;
  duration_ms: number;
  input_tokens: number;
  output_tokens: number;
  status: string;
  summary?: string;
}

export interface MessageItem {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: CitationItem[];
  retrieved_context: any[];
  agent_trace_summary: {
    traces?: AgentTraceItem[];
    duration_ms?: number;
  };
  created_at: string;
}

export interface ConversationItem {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: MessageItem[];
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  query: string;
  answer: string;
  citations: CitationItem[];
  retrieved_contexts: any[];
  agent_traces: AgentTraceItem[];
  total_tokens: number;
  estimated_cost_usd: number;
  total_duration_ms: number;
  is_grounded: boolean;
  confidence: 'high' | 'medium' | 'low';
}

export interface SearchResultItem {
  chunk_id: string;
  document_id: string;
  filename: string;
  chunk_index: number;
  content: string;
  similarity_score: number;
  page_or_row?: string;
  metadata: Record<string, any>;
  retrieval_method: string;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  strategy: string;
  results: SearchResultItem[];
  search_duration_ms: number;
}

export interface MetricOverview {
  total_documents: number;
  indexed_documents: number;
  total_conversations: number;
  total_requests: number;
  avg_latency_ms: number;
  total_tokens: number;
  total_cost_usd: number;
}

export interface AgentPerformance {
  agent_name: string;
  call_count: number;
  avg_duration_ms: number;
  avg_tokens: number;
  error_rate_percent: number;
}

export interface TraceItem {
  id: string;
  request_id: string;
  conversation_id?: string;
  agent_name: string;
  execution_order: number;
  duration_ms: number;
  input_tokens: number;
  output_tokens: number;
  model_name?: string;
  status: string;
  inputs_summary?: Record<string, any>;
  outputs_summary?: Record<string, any>;
  error_message?: string;
  created_at: string;
}

export interface LatencyTrendPoint {
  timestamp: string;
  latency_ms: number;
  token_count: number;
}

export interface MetricsResponse {
  overview: MetricOverview;
  agent_performance: AgentPerformance[];
  recent_traces: TraceItem[];
  latency_trend: LatencyTrendPoint[];
}

export interface EvaluationResultItem {
  id: string;
  question: string;
  ground_truth?: string;
  generated_answer: string;
  faithfulness?: number;
  answer_relevancy?: number;
  context_precision?: number;
  context_recall?: number;
  retrieved_contexts: string[];
}

export interface EvaluationRunResponse {
  id: string;
  run_name: string;
  model_name: string;
  dataset_size: number;
  mean_faithfulness?: number;
  mean_answer_relevancy?: number;
  mean_context_precision?: number;
  mean_context_recall?: number;
  status: string;
  created_at: string;
  results?: EvaluationResultItem[];
}
