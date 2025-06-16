from pydantic import BaseModel, Field
from typing import Optional


class QuestionData(BaseModel):
    query: str = Field(description="user ask question")
    history_length: Optional[int] = Field(
        default=6,
        ge=0,
        le=10,
        description=(
            "how many history length of this  \
             conversation need to consider"
        ),
    )


class AskResponse(BaseModel):
    answer: str = Field(min_length=1, max_length=5000)
