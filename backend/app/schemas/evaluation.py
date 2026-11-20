from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class EvaluationRunRequest(BaseModel):
    run_name: Optional[str] = None
    custom_dataset: Optional[List[Dict[str, Any]]] = None


class EvaluationResultItem(BaseModel):
    id: str
    question: str
    ground_truth: Optional[str]
    generated_answer: str
    faithfulness: Optional[float]
    answer_relevancy: Optional[float]
    context_precision: Optional[float]
    context_recall: Optional[float]
    retrieved_contexts: List[str]
    model_config = ConfigDict(from_attributes=True)


class EvaluationRunResponse(BaseModel):
    id: str
    run_name: str
    model_name: str
    dataset_size: int
    mean_faithfulness: Optional[float]
    mean_answer_relevancy: Optional[float]
    mean_context_precision: Optional[float]
    mean_context_recall: Optional[float]
    status: str
    created_at: datetime
    results: Optional[List[EvaluationResultItem]] = None
    model_config = ConfigDict(from_attributes=True)
