from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T] = []
    size: Optional[int] = None
    status: int = 200
    total: Optional[int] = None
    type: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class ErrorDetail(BaseModel):
    details: Optional[str] = None


class ErrorResponse(BaseModel):
    errors: list[ErrorDetail] = []


class NoContentData(BaseModel):
    details: Optional[str] = None
    message: Optional[str] = None


class NoContentResponse(BaseModel):
    data: list[NoContentData] = []
    size: int = 1
    status: int = 200
    type: str = "no_content"
