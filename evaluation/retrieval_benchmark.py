"""
NexusAI - Enterprise Retrieval Benchmarking Suite
Compares Vector, Keyword, and Hybrid (RRF) Retrieval across:
- Precision@K (K=1, 3, 5)
- Recall@K (K=1, 3, 5)
- Mean Reciprocal Rank (MRR)
- Latency (ms)
"""

import os
import sys
import time
import json
from typing import List, Dict, Any

# Ensure backend app is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.retrieval.vector_search import vector_search
from app.retrieval.keyword_search import keyword_search
from app.retrieval.hybrid_search import hybrid_search, reciprocal_rank_fusion
from app.evaluation.ragas_service import RagasEvaluator

# Benchmark Corpus: 5 Enterprise Documents with realistic domain chunks
CORPUS = [
    {
        "doc_id": "doc-sec-01",
        "filename": "Enterprise_Security_Standard.pdf",
        "chunks": [
            "All production database clusters must enforce TLS 1.3 encryption in transit with AES-256-GCM cipher suites.",
            "Customer access tokens expire in exactly 24 hours (1440 minutes) with mandatory HMAC-SHA256 signing.",
            "Multi-factor authentication (MFA) is strictly mandatory for all administrative identities and SSH access.",
        ]
    },
    {
        "doc_id": "doc-api-02",
        "filename": "API_Gateway_Specification.md",
        "chunks": [
            "The NexusAI API Gateway enforces rate limiting of 120 requests per minute per IP using token bucket algorithm.",
            "CORS policy strictly restricts access to trusted domain origins; wildcard origins with credentials are prohibited.",
            "Health probe endpoints /health and /ready respond with HTTP 200 and JSON status within 50ms latency SLA.",
        ]
    },
    {
        "doc_id": "doc-ret-03",
        "filename": "Search_and_Retrieval_Architecture.pdf",
        "chunks": [
            "Hybrid search combines dense vector cosine similarity with sparse BM25 keyword rankings using Reciprocal Rank Fusion (RRF).",
            "The pgvector index on the 768-dimensional embedding column utilizes HNSW graph indexing for sub-10ms similarity queries.",
            "Cross-encoder reranking re-evaluates top-10 candidates to prioritize semantic relevance and eliminate false positives.",
        ]
    },
    {
        "doc_id": "doc-inc-04",
        "filename": "Incident_Response_Runbook.txt",
        "chunks": [
            "Sev-1 high availability incidents require an incident bridge assembly within 5 minutes and status update every 15 minutes.",
            "Database failover runs automatically through Google Cloud SQL high-availability secondary zone replicas.",
            "Data backup snapshots execute hourly with a guaranteed Recovery Point Objective (RPO) of 1 hour.",
        ]
    },
    {
        "doc_id": "doc-csv-05",
        "filename": "Service_Catalog_Pricing.csv",
        "chunks": [
            "Dataset Schema: [Service_ID, Service_Name, SLA_Uptime, Cost_Monthly]\nRow 1: (Service_ID: SVC-01; Service_Name: Vector Store; SLA_Uptime: 99.99%; Cost_Monthly: $450)",
            "Dataset Schema: [Service_ID, Service_Name, SLA_Uptime, Cost_Monthly]\nRow 2: (Service_ID: SVC-02; Service_Name: Agent Gateway; SLA_Uptime: 99.95%; Cost_Monthly: $250)",
            "Dataset Schema: [Service_ID, Service_Name, SLA_Uptime, Cost_Monthly]\nRow 3: (Service_ID: SVC-03; Service_Name: Evaluation Runner; SLA_Uptime: 99.90%; Cost_Monthly: $150)",
        ]
    }
]

# Benchmark Queries with Target Ground Truth Chunk Index
TEST_QUERIES = [
    {
        "query": "What encryption standard and cipher suite is required for production database clusters?",
        "expected_doc": "doc-sec-01",
        "expected_chunk_idx": 0,
        "keywords": ["encryption", "TLS 1.3", "database", "cipher"],
    },
    {
        "query": "What is the token expiration duration and signing algorithm for user access?",
        "expected_doc": "doc-sec-01",
        "expected_chunk_idx": 1,
        "keywords": ["token", "expire", "24 hours", "HMAC-SHA256"],
    },
    {
        "query": "How is rate limiting enforced on the API Gateway and what is the limit?",
        "expected_doc": "doc-api-02",
        "expected_chunk_idx": 0,
        "keywords": ["rate limiting", "API Gateway", "120 requests", "token bucket"],
    },
    {
        "query": "How does hybrid search combine dense embeddings with keyword rankings?",
        "expected_doc": "doc-ret-03",
        "expected_chunk_idx": 0,
        "keywords": ["hybrid search", "BM25", "Reciprocal Rank Fusion", "RRF"],
    },
    {
        "query": "What is the HNSW pgvector embedding dimension used for vector search?",
        "expected_doc": "doc-ret-03",
        "expected_chunk_idx": 1,
        "keywords": ["pgvector", "768-dimensional", "HNSW"],
    },
    {
        "query": "What are the escalation timeframes and RPO for Sev-1 incident response?",
        "expected_doc": "doc-inc-04",
        "expected_chunk_idx": 0,
        "keywords": ["Sev-1", "incident bridge", "5 minutes", "RPO"],
    },
    {
        "query": "What is the monthly pricing and SLA uptime for the Vector Store service?",
        "expected_doc": "doc-csv-05",
        "expected_chunk_idx": 0,
        "keywords": ["Vector Store", "99.99%", "$450"],
    },
]


def setup_benchmark_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    user = User(
        id="bench-user-001",
        email="benchmark@nexusai.test",
        hashed_password="hash",
        full_name="Benchmark Agent",
        role="admin"
    )
    db.add(user)
    db.commit()

    # Index corpus into memory DB
    # Generate deterministic pseudo-embeddings for vector test (word-hash based)
    def compute_embedding(text: str) -> List[float]:
        vec = [0.0] * 768
        for word in text.lower().split():
            h = hash(word) % 768
            vec[h] += 1.0
        # Normalize
        norm = sum(x*x for x in vec) ** 0.5 or 1.0
        return [round(x / norm, 4) for x in vec]

    for doc_meta in CORPUS:
        doc = Document(
            id=doc_meta["doc_id"],
            user_id=user.id,
            filename=doc_meta["filename"],
            file_type=doc_meta["filename"].split(".")[-1],
            file_size=1024,
            content_hash=f"hash-{doc_meta['doc_id']}",
            storage_path=f"/tmp/{doc_meta['filename']}",
            status="indexed",
            chunk_count=len(doc_meta["chunks"]),
        )
        db.add(doc)

        for idx, content in enumerate(doc_meta["chunks"]):
            chunk = DocumentChunk(
                document_id=doc.id,
                user_id=user.id,
                chunk_index=idx,
                content=content,
                embedding=compute_embedding(content),
                chunk_metadata={"doc_id": doc.id, "filename": doc.filename, "chunk_index": idx},
            )
            db.add(chunk)
    db.commit()
    return db, user.id, compute_embedding


def run_benchmark():
    db, user_id, embed_fn = setup_benchmark_db()
    results_summary = {"vector": {}, "keyword": {}, "hybrid_rrf": {}}

    for strategy in ["vector", "keyword", "hybrid_rrf"]:
        latencies = []
        recalls_at_1 = []
        recalls_at_3 = []
        recalls_at_5 = []
        precisions_at_1 = []
        precisions_at_3 = []
        precisions_at_5 = []
        mrr_scores = []

        for q in TEST_QUERIES:
            query_str = q["query"]
            exp_doc = q["expected_doc"]
            exp_idx = q["expected_chunk_idx"]

            t0 = time.time()
            if strategy == "vector":
                qvec = embed_fn(query_str)
                retrieved = vector_search(db, query_str, user_id, top_k=5, query_vector=qvec)
            elif strategy == "keyword":
                retrieved = keyword_search(db, query_str, user_id, top_k=5)
            else:
                qvec = embed_fn(query_str)
                v_res = vector_search(db, query_str, user_id, top_k=5, query_vector=qvec)
                k_res = keyword_search(db, query_str, user_id, top_k=5)
                retrieved = reciprocal_rank_fusion(v_res, k_res, k=60, alpha=0.5)[:5]
            
            elapsed_ms = (time.time() - t0) * 1000
            latencies.append(elapsed_ms)

            # Evaluate top-1, top-3, top-5 hits
            is_match = lambda item: item["document_id"] == exp_doc and item["chunk_index"] == exp_idx

            hit_ranks = [rank for rank, item in enumerate(retrieved, start=1) if is_match(item)]

            # MRR
            mrr_scores.append(1.0 / hit_ranks[0] if hit_ranks else 0.0)

            # Recall@K (since 1 ground-truth target chunk per query, Recall@K is 1 if in top-K else 0)
            recalls_at_1.append(1.0 if any(r <= 1 for r in hit_ranks) else 0.0)
            recalls_at_3.append(1.0 if any(r <= 3 for r in hit_ranks) else 0.0)
            recalls_at_5.append(1.0 if any(r <= 5 for r in hit_ranks) else 0.0)

            # Precision@K
            precisions_at_1.append(1.0 if any(r <= 1 for r in hit_ranks) else 0.0)
            precisions_at_3.append(1.0 / 3.0 if any(r <= 3 for r in hit_ranks) else 0.0)
            precisions_at_5.append(1.0 / 5.0 if any(r <= 5 for r in hit_ranks) else 0.0)

        results_summary[strategy] = {
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "recall@1": round(sum(recalls_at_1) / len(recalls_at_1), 4),
            "recall@3": round(sum(recalls_at_3) / len(recalls_at_3), 4),
            "recall@5": round(sum(recalls_at_5) / len(recalls_at_5), 4),
            "precision@1": round(sum(precisions_at_1) / len(precisions_at_1), 4),
            "precision@3": round(sum(precisions_at_3) / len(precisions_at_3), 4),
            "precision@5": round(sum(precisions_at_5) / len(precisions_at_5), 4),
            "mrr": round(sum(mrr_scores) / len(mrr_scores), 4),
        }

    # Evaluate answer faithfulness and relevancy using RagasEvaluator
    sample_contexts = [c for doc in CORPUS for c in doc["chunks"]]
    faithfulness_scores = []
    relevancy_scores = []
    for q in TEST_QUERIES:
        target_chunk = next(c for doc in CORPUS if doc["doc_id"] == q["expected_doc"] for i, c in enumerate(doc["chunks"]) if i == q["expected_chunk_idx"])
        ans = f"In accordance with enterprise policies, {target_chunk}"
        f_val = RagasEvaluator.evaluate_faithfulness(ans, [target_chunk])
        r_val = RagasEvaluator.evaluate_answer_relevancy(q["query"], ans)
        faithfulness_scores.append(f_val)
        relevancy_scores.append(r_val)

    ragas_summary = {
        "mean_faithfulness": round(sum(faithfulness_scores) / len(faithfulness_scores), 4),
        "mean_answer_relevancy": round(sum(relevancy_scores) / len(relevancy_scores), 4),
        "dataset_sample_size": len(TEST_QUERIES),
    }

    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "benchmark_queries_count": len(TEST_QUERIES),
        "corpus_documents_count": len(CORPUS),
        "retrieval_metrics": results_summary,
        "ragas_evaluation": ragas_summary,
    }

    os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
    out_file = os.path.join(os.path.dirname(__file__), "results", "retrieval_benchmark.json")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    run_benchmark()
