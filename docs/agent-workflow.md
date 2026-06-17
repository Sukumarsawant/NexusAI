# Multi-Agent Workflow Specification

NexusAI uses a LangGraph state graph with conditional routing and verification feedback loops to guarantee grounded, cited enterprise responses.

---

## 1. Multi-Agent Graph State Machine

```mermaid
flowchart TD
    START([START]) --> QueryAgent["A. Query Understanding Agent"]
    
    QueryAgent --> IntentCheck{"Requires Knowledge Retrieval?"}
    
    IntentCheck -- "No (Greeting / Conversational)" --> ResponseAgent["E. Response Agent"]
    IntentCheck -- "Yes (Analytical / Factual)" --> RetrievalAgent["B. Retrieval Agent"]
    
    RetrievalAgent --> SufficiencyCheck{"Context Sufficient?"}
    
    SufficiencyCheck -- "Insufficient & Retries < Limit" --> RetrievalAgent
    SufficiencyCheck -- "Sufficient or Limit Reached" --> ReasoningAgent["C. Reasoning Agent"]
    
    ReasoningAgent --> VerificationAgent["D. Verification Agent"]
    
    VerificationAgent --> VerificationCheck{"Passed Grounding Audit?"}
    
    VerificationCheck -- "Failed & Retries < Limit" -->|Critique Feedback Loop| RetrievalAgent
    VerificationCheck -- "Passed or Retries Exceeded" --> ResponseAgent
    
    ResponseAgent --> END([END])
```

---

## 2. Agent Responsibilities & Output Contracts

### A. Query Understanding Agent
- **Inputs**: User raw query string, conversation history.
- **Actions**:
  - Classifies intent (`factual_inquiry`, `comparison`, `summarization`, `general_conversation`).
  - Classifies question type (`factoid`, `complex_reasoning`, `exploratory`, `conversational`).
  - Extracts key entities.
  - Rewrites ambiguous questions into search-optimized dense keyword queries.
- **Routing**: Bypasses retrieval for pure conversational queries; routes to Retrieval Agent otherwise.

### B. Retrieval Agent
- **Inputs**: Rewritten query, document filters, user ID.
- **Actions**:
  - Calls `RetrievalEngine.search` (Vector + Keyword + RRF).
  - Evaluates context sufficiency score against user intent.
- **Routing**: If retrieved context is insufficient and `retrieval_cycle < MAX_RETRIES`, re-queries with broadened search terms.

### C. Reasoning Agent
- **Inputs**: Retrieved excerpts with source filenames and page/row indices.
- **Actions**:
  - Synthesizes information across multiple documents.
  - Identifies contradictions or discrepancies across sources.
  - Formulates a preliminary draft strictly supported by retrieved text.

### D. Verification Agent (Grounding Auditor)
- **Inputs**: Reasoning draft, retrieved source context, original question.
- **Actions**:
  - Audits each claim in the draft against the retrieved context.
  - Extracts ungrounded claims or numerical extrapolations.
  - Flags whether the draft passes strict grounding criteria.
- **Routing**: If unsupported claims exist and `retry_count < MAX_RETRIES`, loops back to Retrieval/Reasoning with critique feedback.

### E. Response Agent
- **Inputs**: Verified draft, citations list, contradictions noted.
- **Actions**:
  - Structures final markdown answer with professional enterprise headings.
  - Injects verifiable inline citations `[Source X: filename, Page/Row Y]`.
  - Distinguishes verified facts from residual uncertainty.
