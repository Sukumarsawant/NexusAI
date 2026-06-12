import {
  AuthResponse,
  User,
  DocumentItem,
  ConversationItem,
  ChatResponse,
  SearchResponse,
  MetricsResponse,
  MetricOverview,
  EvaluationRunResponse,
} from '../types';

const API_BASE = '/api';

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('nexus_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    ...getAuthHeader(),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Auth
  async register(data: { email: string; password: string; full_name?: string }): Promise<AuthResponse> {
    return request<AuthResponse>('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async login(data: { email: string; password: string }): Promise<AuthResponse> {
    return request<AuthResponse>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async getMe(): Promise<User> {
    return request<User>('/auth/me');
  },

  // Documents
  async listDocuments(): Promise<DocumentItem[]> {
    return request<DocumentItem[]>('/documents');
  },

  async uploadDocument(file: File, chunkSize = 800, chunkOverlap = 150): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('chunk_size', chunkSize.toString());
    formData.append('chunk_overlap', chunkOverlap.toString());

    return request<DocumentItem>('/documents/upload', {
      method: 'POST',
      body: formData,
    });
  },

  async deleteDocument(id: string): Promise<{ message: string; id: string }> {
    return request<{ message: string; id: string }>(`/documents/${id}`, {
      method: 'DELETE',
    });
  },

  async reindexDocument(id: string): Promise<{ message: string; chunk_count: number }> {
    return request<{ message: string; chunk_count: number }>(`/documents/${id}/reindex`, {
      method: 'POST',
    });
  },

  // Search & Retrieval
  async search(query: string, strategy = 'hybrid', top_k = 5, alpha = 0.5): Promise<SearchResponse> {
    return request<SearchResponse>('/retrieval/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, strategy, top_k, alpha }),
    });
  },

  // Chat & Multi-Agent
  async sendChat(query: string, conversationId?: string, top_k = 5): Promise<ChatResponse> {
    return request<ChatResponse>('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, conversation_id: conversationId, top_k }),
    });
  },

  async listConversations(): Promise<ConversationItem[]> {
    return request<ConversationItem[]>('/conversations');
  },

  async getConversation(id: string): Promise<ConversationItem> {
    return request<ConversationItem>(`/conversations/${id}`);
  },

  async deleteConversation(id: string): Promise<{ message: string }> {
    return request<{ message: string }>(`/conversations/${id}`, {
      method: 'DELETE',
    });
  },

  // Observability
  async getMetrics(): Promise<MetricsResponse> {
    return request<MetricsResponse>('/observability/metrics');
  },

  async getOverview(): Promise<MetricOverview> {
    return request<MetricOverview>('/observability/overview');
  },

  // Evaluation
  async runEvaluation(runName?: string): Promise<EvaluationRunResponse> {
    return request<EvaluationRunResponse>('/evaluation/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ run_name: runName }),
    });
  },

  async getEvaluationHistory(): Promise<EvaluationRunResponse[]> {
    return request<EvaluationRunResponse[]>('/evaluation/results');
  },

  async getEvaluationDetail(runId: string): Promise<EvaluationRunResponse> {
    return request<EvaluationRunResponse>(`/evaluation/results/${runId}`);
  },

  // System
  async checkHealth(): Promise<{ status: string }> {
    const res = await fetch('/health');
    return res.json();
  },

  async checkReadiness(): Promise<{ status: string; gemini_api_configured: boolean; active_model: string }> {
    const res = await fetch('/ready');
    return res.json();
  },
};
