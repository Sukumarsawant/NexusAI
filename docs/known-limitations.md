# NexusAI — Known Limitations & Architectural Boundaries

**Document Purpose:** Transparent documentation of current platform boundaries, edge cases, and architectural trade-offs.  
**Audience:** Platform Engineers, Security Auditors, and Production SREs.  
**Last Updated:** November 20, 2026  

---

## 1. Database & Vector Index Runtime Parity

### SQLite vs PostgreSQL Runtime Behavior
- **Design:** NexusAI supports both PostgreSQL (with the `pgvector` extension) and an in-memory SQLite fallback via `SafeVector` (`backend/app/models/custom_types.py`).
- **Limitation:** In SQLite mode (used for lightweight local testing or automated unit tests), pgvector's raw SQL cosine operator `<=>` is not available. The application falls back to Python-level cosine distance calculation. For large production datasets (>100,000 chunks), PostgreSQL with pgvector and HNSW indexing (`init-pgvector.sql`) is strictly required to maintain sub-15ms retrieval latencies.

---

## 2. LangGraph Checkpointing & State Persistence

### In-Memory MemorySaver vs PostgresSaver
- **Current State:** The multi-agent workflow in `backend/app/agents/workflow.py` compiles with `langgraph.checkpoint.memory.MemorySaver()`.
- **Impact:**
  - Conversation metadata, user query history, assistant responses, citations, and agent traces are fully persisted in PostgreSQL (`conversations`, `messages`, `agent_traces`).
  - However, if the FastAPI server restarts in the middle of an in-flight LangGraph multi-agent loop, the partial graph execution state is not resumable from disk.
- **Production Recommendation:** Integrate `langgraph.checkpoint.postgres.PostgresSaver` backed by a dedicated PostgreSQL checkpoint schema to enable mid-workflow resume capabilities.

---

## 3. Gemini API Quotas & Rate Limits

### Free Tier vs Enterprise Tier Considerations
- **Behavior:** The platform uses the official `google-genai` SDK with automated model fallback (`gemini-3.5-flash` -> `gemini-3.1-flash-lite`).
- **Limitation:** On free-tier Google AI Studio API keys, aggressive concurrency or multi-step agent reasoning can trigger HTTP 429 Too Many Requests or HTTP 503 Service Unavailable during peak hours.
- **Production Recommendation:** For enterprise production deployments, configure Google Cloud Vertex AI credentials with provisioned throughput to guarantee deterministic low-latency SLAs.

---

## 4. Client-Side Token Storage

### LocalStorage vs HttpOnly Cookies
- **Current State:** The frontend React dashboard stores the JWT access token in browser `localStorage`.
- **Limitation:** Tokens stored in `localStorage` are vulnerable to Cross-Site Scripting (XSS) if an untrusted third-party dependency is introduced.
- **Production Recommendation:** Transition to `Set-Cookie` with `HttpOnly; Secure; SameSite=Strict` for production deployments behind a reverse proxy (e.g. Nginx or Cloud Run Custom Domain).

---

## 5. Document Ingestion Size & OCR Capabilities

### Scanned PDF Limitations
- **Current State:** The PDF extractor (`backend/app/ingestion/extractors.py`) uses `pypdf` for text extraction.
- **Limitation:** Scanned PDFs that contain only rasterized bitmap images without an embedded text layer will yield zero extractable text chunks.
- **Production Recommendation:** Integrate Google Cloud Document AI or Tesseract OCR for automatic fallback processing of scanned image-only PDFs.

---

## 6. OpenTelemetry Distributed Tracing

### Console Exporter vs Remote OTLP Collector
- **Current State:** The backend configures OpenTelemetry using `SimpleSpanProcessor` and `ConsoleSpanExporter` (`backend/app/observability/tracer.py`).
- **Limitation:** Trace spans are printed to stdout rather than dispatched via gRPC to an external APM collector.
- **Production Recommendation:** Provide `OTEL_EXPORTER_OTLP_ENDPOINT` in `docker-compose.yml` and wire `OTLPSpanExporter` to ship traces to Google Cloud Trace, Jaeger, or Datadog.
