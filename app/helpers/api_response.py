from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    details: Optional[Any] = None


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
