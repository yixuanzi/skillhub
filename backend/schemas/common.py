from pydantic import BaseModel
from typing import List, TypeVar, Generic

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict = {}

class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "Operation successful"
