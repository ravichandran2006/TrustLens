from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    content: str = Field(min_length=1)
    document_type: str = Field(default="agreement")


class QuestionRequest(BaseModel):
    agreement_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
