from typing import List, Dict, Any

ENTERPRISE_EVALUATION_DATASET: List[Dict[str, Any]] = [
    {
        "id": "eval-001",
        "question": "What is the data retention policy for financial transaction records under SOC2?",
        "ground_truth": "Financial transaction records must be retained for a minimum of 7 years in write-once-read-many (WORM) compliant storage, with annual audits.",
        "contexts": [
            "SOC2 Compliance Handbook Section 4.2: All financial transaction records and ledger logs must be retained for at least 7 years in immutable WORM storage. Periodic compliance reviews are performed annually."
        ]
    },
    {
        "id": "eval-002",
        "question": "How does NexusAI enforce user isolation in multi-tenant document retrieval?",
        "ground_truth": "NexusAI enforces user isolation by filtering every vector and keyword query with the authenticated user's ID at the database query level.",
        "contexts": [
            "NexusAI Security Whitepaper: Tenant isolation is guaranteed by mandatory user_id foreign key constraints on documents and document_chunks. All SQL and pgvector queries include user_id = :user_id filtering."
        ]
    },
    {
        "id": "eval-003",
        "question": "What is the maximum allowed file size for document uploads?",
        "ground_truth": "The platform accepts document uploads up to 50MB per file for PDF, TXT, Markdown, and CSV formats.",
        "contexts": [
            "System Architecture Specification: File uploads are validated at the API gateway with a hard ceiling of 50MB. Supported MIME types include PDF, TXT, MD, and CSV."
        ]
    },
    {
        "id": "eval-004",
        "question": "Which embedding model and dimensionality does NexusAI utilize for vector representations?",
        "ground_truth": "NexusAI utilizes Google Gemini text-embedding-004 with 768-dimensional vector embeddings stored in PostgreSQL via pgvector.",
        "contexts": [
            "AI Pipeline Documentation: Embeddings are generated using the Google GenAI SDK with text-embedding-004, producing 768-dimension vectors indexed via pgvector IVFFlat/HNSW."
        ]
    },
    {
        "id": "eval-005",
        "question": "How does the Verification Agent handle hallucinated or ungrounded claims?",
        "ground_truth": "The Verification Agent identifies unsupported claims, rejects unverified conclusions, and triggers a retry cycle back to retrieval or outputs an insufficiency notice.",
        "contexts": [
            "Multi-Agent LangGraph Specification: The Verification Agent cross-examines proposed answers against retrieved excerpts. If ungrounded claims exceed the threshold, it triggers a retry loop up to the retry limit."
        ]
    }
]
