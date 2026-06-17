# NexusAI — Enterprise Multi-Agent RAG Platform

[![CI Backend Tests](https://img.shields.io/badge/pytest-passing-brightgreen.svg)]()
[![Frontend Build](https://img.shields.io/badge/vite-passing-brightgreen.svg)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-blue.svg)]()
[![Gemini API](https://img.shields.io/badge/Google%20GenAI-3.8%20Flash-orange.svg)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-purple.svg)]()

> **NexusAI** is a production-oriented Enterprise Multi-Agent Retrieval-Augmented Generation (RAG) Platform. It ingests structured (CSV) and unstructured (PDF, TXT, Markdown) enterprise documents, executes hybrid vector/keyword retrieval, orchestrates specialized LangGraph agents, verifies answers against retrieved evidence to eliminate hallucinations, and provides granular OpenTelemetry observability into the entire execution pipeline.

---

## 1. Project Overview

NexusAI is designed to address the challenges of deploying AI intelligence in high-stakes enterprise environments. Traditional naive RAG architectures suffer from:
- Chunking that destroys tabular schema in CSVs.
- Single-point vector retrieval blindness when queries require exact keyword matches.
- Hallucinated or speculative answers when retrieved context is incomplete.
- A lack of auditability into intermediate agent reasoning and token expenses.

NexusAI solves these problems by decoupling query understanding, retrieval, reasoning, grounding verification, and response generation into a coordinated multi-agent state machine built on **LangGraph**, backed by **PostgreSQL 16 with pgvector**, and powered by the **Google Gemini GenAI SDK**.

---

## 2. Problem Statement

Enterprises cannot rely on black-box chatbots for critical business decisions. If an LLM fabricates a financial number, quotes a non-existent corporate policy, or leaks data across tenant boundaries, the liability is immense. 

NexusAI enforces:
1. **Verifiable Grounding**: Every answer claim is audited by a Verification Agent against retrieved context; unsupported conclusions are rejected or routed for additional retrieval.
2. **Tabular Context Preservation**: CSV files are converted into structured row-column schema chunks rather than flattened into disorganized prose.
3. **True Hybrid Retrieval**: Blends pgvector cosine similarity (`<=>`) and PostgreSQL full-text search (`to_tsvector`, `websearch_to_tsquery`) using Reciprocal Rank Fusion (RRF).
4. **Tenant Isolation**: Strict `user_id` query scoping prevents users from accessing unauthorized documents.
5. **Full Observability**: Provider-reported token counts, latencies, and step-by-step agent traces are stored in PostgreSQL for cost tracking and performance analysis.

---

## 3. High-Level Architecture Diagram

```mermaid
flowchart TD
    User["Enterprise User / Web Client"] -->|HTTPS / REST| API["FastAPI Gateway"]

    subgraph Security ["Security & Auth Layer"]
        API --> Auth["JWT Auth & Tenant Isolation (user_id)"]
    end

    subgraph IngestionPipeline ["Document Ingestion Pipeline"]
        Upload["Upload (PDF, CSV, MD, TXT)"] --> Hash["SHA-256 Deduplication"]
        Hash --> Extract["Structure & Row Extractor"]
        Extract --> Chunk["Recursive Semantic Chunker"]
        Chunk --> Embed["Gemini text-embedding-004"]
    end

    subgraph Storage ["PostgreSQL 16 Storage"]
        Embed --> PGVector["pgvector (Cosine Distance <=> )"]
        Extract --> FTS["PostgreSQL Full-Text Search (tsvector)"]
        Auth --> DBUsers["Users & Conversations"]
        MetricsStore["Request Metrics & Agent Traces"]
    end

    subgraph RetrievalEngine ["Hybrid Retrieval Engine"]
        VectorSearch["Vector Similarity Search"]
        KeywordSearch["Keyword Full-Text Search"]
        VectorSearch & KeywordSearch --> RRF["Reciprocal Rank Fusion (RRF)"]
        RRF --> Rerank["Cross-Score Semantic Reranker"]
    end

    subgraph LangGraphAgents ["LangGraph Multi-Agent Orchestration"]
        QAgent["Query Understanding Agent"]
        RAgent["Retrieval Agent"]
        ReasonAgent["Reasoning Agent"]
        VerifyAgent["Verification Agent"]
        RespAgent["Response Agent"]

        QAgent --> RAgent
        RAgent --> ReasonAgent
        ReasonAgent --> VerifyAgent
        VerifyAgent -->|Ungrounded: Feedback Loop| RAgent
        VerifyAgent -->|Approved| RespAgent
    end

    Auth --> IngestionPipeline
    Auth --> LangGraphAgents
    RAgent <--> RetrievalEngine
    RetrievalEngine <--> PGVector & FTS
    LangGraphAgents --> MetricsStore
```

---

## 4. Technology Stack

### Backend
- **Python**: 3.12+
- **FastAPI**: Asynchronous web framework with Pydantic validation
- **SQLAlchemy 2.0**: ORM and query builder with connection pooling
- **PostgreSQL 16 & pgvector**: Vector similarity (`<=>`) and full-text keyword search (`to_tsvector`)
- **PyPDF & CSV**: Structure-preserving extractors

### AI & Agents
- **Google GenAI SDK**: Official `google-genai` Python SDK
- **Gemini 2.5 Flash**: Orchestration, reasoning, query analysis, and verification
- **text-embedding-004**: 768-dimensional embeddings
- **LangGraph**: Directed cyclic agent workflow orchestration with checkpointing
- **RAGAS Evaluator**: Faithfulness, Answer Relevancy, Context Precision, Context Recall

### Frontend
- **React 18 & TypeScript**: Strongly-typed user interface
- **Vite 6**: Fast bundling and build system
- **Tailwind CSS**: Professional enterprise styling with dark/light themes
- **Recharts**: Telemetry charts for latency and agent duration
- **Lucide React**: Clean enterprise iconography

### Infrastructure & Deployment
- **Docker & Docker Compose**: Local containerized stack
- **Google Cloud Run**: Serverless container hosting
- **Cloud SQL for PostgreSQL**: Managed database with pgvector
- **Google Cloud Storage (GCS)**: Scalable cloud document storage
- **Terraform**: Declarative Infrastructure as Code

---

## 5. System Workflow

1. **Document Upload**:
   - Client sends file (PDF, TXT, MD, CSV) to `POST /api/documents/upload`.
   - File size (<50MB) and MIME type are validated.
   - SHA-256 hash is computed; duplicate uploads for the tenant are rejected with HTTP 409.
   - Content is extracted, maintaining section headers, page numbers, and CSV row-column schemas.
   - Text is chunked with configurable size and overlap.
   - Vector embeddings are generated using `text-embedding-004` and stored in PostgreSQL with pgvector.
2. **Query Processing & Retrieval**:
   - Query Understanding Agent extracts entities and determines if retrieval is required.
   - Retrieval Agent executes hybrid search (pgvector cosine + PostgreSQL keyword search) fused via Reciprocal Rank Fusion (RRF).
   - If retrieved context is insufficient, an additional retrieval cycle is triggered.
3. **Reasoning & Grounding Verification**:
   - Reasoning Agent synthesizes retrieved snippets and notes contradictions.
   - Verification Agent cross-examines all claims against source passages.
   - If hallucinations are detected, the workflow loops back to retrieval with critique feedback.
4. **Response & Citation Generation**:
   - Response Agent compiles markdown with explicit citations `[Source X: filename, Page/Row Y]`.
   - Complete trace and token metrics are written to `request_metrics` and `agent_traces`.

---

## 6. Multi-Agent Architecture

```mermaid
flowchart TD
    START([START]) --> QueryAgent["A. Query Understanding Agent"]
    
    QueryAgent --> IntentCheck{"Requires Retrieval?"}
    IntentCheck -- "No (Greeting)" --> ResponseAgent["E. Response Agent"]
    IntentCheck -- "Yes (Analytical)" --> RetrievalAgent["B. Retrieval Agent"]
    
    RetrievalAgent --> SufficiencyCheck{"Context Sufficient?"}
    SufficiencyCheck -- "Insufficient" --> RetrievalAgent
    SufficiencyCheck -- "Sufficient" --> ReasoningAgent["C. Reasoning Agent"]
    
    ReasoningAgent --> VerificationAgent["D. Verification Agent"]
    
    VerificationAgent --> VerificationCheck{"Grounding Passed?"}
    VerificationCheck -- "Failed (Unsupported Claims)" -->|Critique Loop| RetrievalAgent
    VerificationCheck -- "Passed" --> ResponseAgent
    
    ResponseAgent --> END([END])
```

| Agent | Core Responsibility |
|---|---|
| **Query Understanding Agent** | Intent classification, entity extraction, search query rewriting |
| **Retrieval Agent** | Hybrid search execution, context sufficiency audit |
| **Reasoning Agent** | Evidence synthesis, identifying discrepancies across sources |
| **Verification Agent** | Hallucination detection, citation verification, rejection of ungrounded assertions |
| **Response Agent** | Enterprise typography, source citation attribution, uncertainty communication |

---

## 7. Database Schema

- `users`: User identity, hashed passwords (bcrypt), roles, and tenant boundaries.
- `documents`: Document metadata, storage paths, file type, file size, content hash, and status (`pending`, `processing`, `indexed`, `failed`).
- `document_chunks`: Document chunks, chunk index, text content, 768-dim `pgvector` embedding, and metadata (page numbers, row numbers, headers).
- `conversations`: Conversation sessions scoped to user ID.
- `messages`: Multi-turn message history with citations, retrieved context, and execution summaries.
- `request_metrics`: End-to-end request duration, input/output tokens, total tokens, and estimated cost in USD.
- `agent_traces`: Step-by-step agent node execution records (order, duration, tokens, status, summaries).
- `evaluation_runs` & `evaluation_results`: RAGAS benchmark scores and per-question ground truth comparisons.

---

## 8. API Documentation

### Authentication
- `POST /api/auth/register`: Register new user account.
- `POST /api/auth/login`: Authenticate and receive JWT bearer token.
- `GET /api/auth/me`: Get current authenticated user profile.

### Documents
- `POST /api/documents/upload`: Upload and ingest PDF, TXT, MD, or CSV file.
- `GET /api/documents`: List documents owned by the authenticated tenant.
- `GET /api/documents/{id}`: Get document details and indexing status.
- `DELETE /api/documents/{id}`: Delete document and cascade delete all chunks.
- `POST /api/documents/{id}/reindex`: Re-chunk and re-embed existing document.

### Chat & Multi-Agent
- `POST /api/chat`: Execute multi-agent LangGraph workflow for a query.
- `GET /api/conversations`: List multi-turn conversation sessions.
- `GET /api/conversations/{id}`: Get full message history and citations.
- `DELETE /api/conversations/{id}`: Delete conversation session.

### Retrieval & Observability
- `POST /api/retrieval/search`: Probe hybrid retrieval directly.
- `GET /api/observability/metrics`: Complete telemetry (overview, agent durations, latency trends).
- `GET /api/observability/traces`: List individual agent node execution traces.

### Evaluation
- `POST /api/evaluation/run`: Trigger automated RAGAS benchmark across enterprise QA dataset.
- `GET /api/evaluation/results`: Retrieve historical benchmark runs and metric scores.

### Health
- `GET /health`: Liveness probe.
- `GET /ready`: Readiness probe verifying database and Gemini API status.

---

## 9. Local Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 20+ and pnpm
- PostgreSQL with pgvector (or Docker)

### Step 1: Clone and Configure
```bash
git clone https://github.com/enterprise/nexusai.git
cd nexusai
cp .env.example .env
# Edit .env and supply your GEMINI_API_KEY
```

### Step 2: Run Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Backend runs at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

### Step 3: Run Frontend
```bash
cd frontend
pnpm install
pnpm run dev
```
Frontend runs at `http://localhost:5173`.

---

## 10. Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API Key | *Required for live inference* |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/nexusai` |
| `JWT_SECRET` | Secret key for JWT signing | `nexusai_enterprise_secure_token_key` |
| `GEMINI_MODEL` | Gemini LLM model identifier | `gemini-2.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Gemini Embedding model | `text-embedding-004` |
| `DEFAULT_CHUNK_SIZE` | Target chunk size (characters) | `800` |
| `DEFAULT_CHUNK_OVERLAP` | Chunk overlap (characters) | `150` |
| `HYBRID_ALPHA` | Weight between vector (1.0) and keyword (0.0) | `0.5` |
| `MAX_AGENT_RETRIES` | Max loops on insufficient context / ungrounded claims | `2` |

---

## 11. Docker Setup

To start the entire application (PostgreSQL + pgvector, Backend, Frontend) with a single command:

```bash
docker compose up --build
```

Persistent database data is stored in the Docker volume `pgdata`.

---

## 12. Google Cloud Platform Deployment

1. **Deploy with Script**:
   ```bash
   ./infrastructure/gcp/deploy-gcp.sh <PROJECT_ID> us-central1
   ```
2. **Deploy with Terraform**:
   ```bash
   cd infrastructure/gcp/terraform
   terraform init
   terraform apply -var="project_id=<PROJECT_ID>" -var="gemini_api_key=<API_KEY>" -var="db_password=<PASSWORD>"
   ```

Detailed instructions and IAM roles are documented in [docs/deployment.md](docs/deployment.md).

---

## 13. Evaluation Methodology

NexusAI implements standard RAGAS evaluation metrics:
- **Faithfulness**: Proportion of factual claims in the answer that can be inferred directly from the retrieved context passages.
- **Answer Relevancy**: Measure of how directly and completely the generated answer addresses the question.
- **Context Precision**: Rank-weighted precision indicating whether relevant context chunks appear at the highest retrieval positions.
- **Context Recall**: Extent to which ground truth knowledge is captured within retrieved context chunks.

Evaluations can be triggered via `POST /api/evaluation/run` or directly through the Evaluation tab in the frontend dashboard. Results are persisted in the database and displayed with actual calculated scores.

---

## 14. Observability Metrics

The platform captures:
- Provider-reported token usage (`usage_metadata.prompt_token_count` and `candidates_token_count`).
- Execution duration per agent node in milliseconds.
- Dynamic cost calculations based on configurable model pricing tiers ($0.15/1M input, $0.60/1M output for Gemini 2.5 Flash).
- End-to-end request latencies and error rates visualized with Recharts.

---

## 15. Known Limitations

1. **Live Gemini Credentials Requirement**: The multi-agent LangGraph workflow requires a valid `GEMINI_API_KEY` to perform live LLM reasoning and embedding generation. When credentials are not supplied, the platform falls back to structured heuristics and zero-embeddings for testing.
2. **OCR for Scanned PDFs**: PDF extraction utilizes `pypdf`, extracting embedded text streams. Scanned image-only PDFs require an upstream OCR pre-processor.
3. **Database Extension Permissions**: The `vector` extension in PostgreSQL requires superuser or `cloudsql.enable_pgvector` permission on Cloud SQL.
