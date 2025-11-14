from pydantic import BaseModel
from typing import Optional


class ExplanationRequest(BaseModel):
    code: str
    language: Optional[str] = "auto"


class ExplanationResponse(BaseModel):
    success: bool
    explanation: str
    language: str
