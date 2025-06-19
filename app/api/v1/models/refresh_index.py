from pydantic import BaseModel, Field
from enum import Enum


# Define the Enum for index_target
class IndexTargetEnum(str, Enum):
    API_DOCS = "api_docs"


# Extend the Pydantic model
class RefreshIndexQueryParams(BaseModel):
    index_target: IndexTargetEnum = Field(
        description="target docs for the reindex", default=IndexTargetEnum.API_DOCS
    )
