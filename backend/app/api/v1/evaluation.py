from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.evaluation import EvaluationRun
from app.schemas.evaluation import EvaluationRunRequest, EvaluationRunResponse
from app.evaluation.runner import EvaluationRunner

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.post("/run", response_model=EvaluationRunResponse)
def run_evaluation(
    req: EvaluationRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run_obj = EvaluationRunner.run_benchmark(
        db=db,
        run_name=req.run_name,
        custom_dataset=req.custom_dataset,
    )
    return EvaluationRunResponse.model_validate(run_obj)


@router.get("/results", response_model=List[EvaluationRunResponse])
def get_evaluation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    runs = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()
    return [EvaluationRunResponse.model_validate(r) for r in runs]


@router.get("/results/{run_id}", response_model=EvaluationRunResponse)
def get_evaluation_run_detail(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found")
    return EvaluationRunResponse.model_validate(run)
