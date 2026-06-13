from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.application.dto.requests import QuestionRequest
from app.application.dto.responses import QuestionResponse
from app.application.use_cases.answer_question import AnswerQuestionUseCase
from app.infrastructure.dependencies import get_question_use_case

router = APIRouter(prefix="/api", tags=["questions"])


@router.post("/question", response_model=QuestionResponse)
def ask_question(
    payload: QuestionRequest,
    use_case: AnswerQuestionUseCase = Depends(get_question_use_case),
) -> QuestionResponse:
    if not payload.agreement_id.strip():
        raise HTTPException(status_code=400, detail="agreement_id is required")
    result = use_case.execute(agreement_id=payload.agreement_id, question=payload.question)
    return QuestionResponse(answer=result.answer, sources=result.sources, metadata={"agreement_id": payload.agreement_id})
