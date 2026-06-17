# Database Design & Schema Specification

NexusAI uses PostgreSQL 16 with the `pgvector` extension. A cross-platform abstraction (`SafeVector`) is provided for development and test execution.

---

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ DOCUMENTS : "owns"
    USERS ||--o{ CONVERSATIONS : "creates"
    USERS ||--o{ REQUEST_METRICS : "executes"
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : "contains"
    CONVERSATIONS ||--o{ MESSAGES : "contains"
    EVALUATION_RUNS ||--o{ EVALUATION_RESULTS : "produces"

    USERS {
        string id PK
        string email UK
        string hashed_password
        string full_name
        string role
        boolean is_active
        datetime created_at
    }

    DOCUMENTS {
        string id PK
        string user_id FK
        string filename
        string file_type
        bigint file_size
        string content_hash
        string storage_path
        string status
        int chunk_count
        json doc_metadata
        datetime created_at
    }

    DOCUMENT_CHUNKS {
        string id PK
        string document_id FK
        string user_id FK
        int chunk_index
        text content
        vector embedding
        json chunk_metadata
        datetime created_at
    }

    CONVERSATIONS {
        string id PK
        string user_id FK
        string title
        datetime created_at
        datetime updated_at
    }

    MESSAGES {
        string id PK
        string conversation_id FK
        string role
        text content
        json citations
        json retrieved_context
        json agent_trace_summary
        datetime created_at
    }

    REQUEST_METRICS {
        string id PK
        string request_id
        string conversation_id
        string user_id
        string endpoint
        float total_duration_ms
        int input_tokens
        int output_tokens
        int total_tokens
        float estimated_cost_usd
        datetime created_at
    }

    AGENT_TRACES {
        string id PK
        string request_id
        string conversation_id
        string agent_name
        int execution_order
        float duration_ms
        int input_tokens
        int output_tokens
        string status
        json inputs_summary
        json outputs_summary
        datetime created_at
    }

    EVALUATION_RUNS {
        string id PK
        string run_name
        string model_name
        int dataset_size
        float mean_faithfulness
        float mean_answer_relevancy
        float mean_context_precision
        float mean_context_recall
        string status
        datetime created_at
    }

    EVALUATION_RESULTS {
        string id PK
        string run_id FK
        text question
        text ground_truth
        text generated_answer
        json retrieved_contexts
        float faithfulness
        float answer_relevancy
        float context_precision
        float context_recall
        datetime created_at
    }
```

---

## 2. Multi-Tenant Isolation
Every query to `documents`, `document_chunks`, and `conversations` enforces tenant boundary isolation by joining or filtering on `user_id = :current_user_id`. Users cannot view or query documents belonging to another user.

## 3. Vector & Full-Text Search Indices
- **pgvector Index**: IVFFlat or HNSW cosine index on `document_chunks.embedding` using cosine distance `<=>`.
- **Full-Text Index**: GIN index on `to_tsvector('english', content)` for sub-millisecond keyword matching.
- **Content Hash Index**: Compound index on `(user_id, content_hash)` prevents duplicate file uploads.
