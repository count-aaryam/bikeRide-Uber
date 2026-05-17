from fastapi import Query
from typing import TypeVar, List
from dataclasses import dataclass

@dataclass
class PaginationParams:
    """
    Reusable pagination dependency.
    Inject with Depends(get_pagination).
    """
    page: int
    limit: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit

def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=10, ge=1, le=100, description="Items per page")
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)

def paginate_response(data: List, total: int, pagination: PaginationParams) -> dict:
    """
    Wraps paginated data with metadata.
    Always returns the same shape for every list endpoint.
    """
    total_pages = (total + pagination.limit - 1) // pagination.limit

    return {
        "items": data,
        "pagination": {
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit,
            "total_pages": total_pages,
            "has_next": pagination.page < total_pages,
            "has_prev": pagination.page > 1
        }
    }