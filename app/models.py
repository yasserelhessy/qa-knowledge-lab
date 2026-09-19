from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=500)

    @field_validator("question")
    @classmethod
    def meaningful(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Enter at least three non-space characters")
        return value

class Source(BaseModel):
    id: str
    title: str
    excerpt: str

class Answer(BaseModel):
    answer: str
    status: Literal["answered", "refused"]
    sources: list[Source]
    mode: Literal["demo", "openai"]
    retrieval_score: float
