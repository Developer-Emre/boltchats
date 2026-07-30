"""
MongoDB Query Builders for filtering, sorting, pagination
"""

from datetime import datetime
from enum import Enum
from typing import Any


class SortOrder(str, Enum):
    """Sort order for queries"""
    ASC = 1
    DESC = -1


class QueryBuilder:
    """Builder for MongoDB queries with fluent API"""

    def __init__(self):
        self.filter: dict = {}
        self.sort: list[tuple[str, int]] = []
        self.skip_count: int = 0
        self.limit_count: int = 100

    def filter_by(self, **kwargs) -> "QueryBuilder":
        """Add filter conditions (AND logic).
        
        Examples:
            .filter_by(organization_id="123", status="open")
        """
        self.filter.update(kwargs)
        return self

    def filter_in(self, field: str, values: list) -> "QueryBuilder":
        """Add $in filter condition.
        
        Args:
            field: Field name
            values: List of values to match
        """
        self.filter[field] = {"$in": values}
        return self

    def filter_eq(self, field: str, value: Any) -> "QueryBuilder":
        """Add equality filter.
        
        Args:
            field: Field name
            value: Value to match
        """
        self.filter[field] = value
        return self

    def filter_ne(self, field: str, value: Any) -> "QueryBuilder":
        """Add not-equal filter.
        
        Args:
            field: Field name
            value: Value to exclude
        """
        if field not in self.filter:
            self.filter[field] = {}
        self.filter[field]["$ne"] = value
        return self

    def filter_gt(self, field: str, value: Any) -> "QueryBuilder":
        """Add greater-than filter.
        
        Args:
            field: Field name
            value: Comparison value
        """
        if field not in self.filter:
            self.filter[field] = {}
        self.filter[field]["$gt"] = value
        return self

    def filter_gte(self, field: str, value: Any) -> "QueryBuilder":
        """Add greater-than-or-equal filter."""
        if field not in self.filter:
            self.filter[field] = {}
        self.filter[field]["$gte"] = value
        return self

    def filter_lt(self, field: str, value: Any) -> "QueryBuilder":
        """Add less-than filter."""
        if field not in self.filter:
            self.filter[field] = {}
        self.filter[field]["$lt"] = value
        return self

    def filter_lte(self, field: str, value: Any) -> "QueryBuilder":
        """Add less-than-or-equal filter."""
        if field not in self.filter:
            self.filter[field] = {}
        self.filter[field]["$lte"] = value
        return self

    def filter_exists(self, field: str, exists: bool = True) -> "QueryBuilder":
        """Add exists filter.
        
        Args:
            field: Field name
            exists: Whether field should exist
        """
        if field not in self.filter:
            self.filter[field] = {}
        self.filter[field]["$exists"] = exists
        return self

    def filter_regex(self, field: str, pattern: str, options: str = "") -> "QueryBuilder":
        """Add regex filter.
        
        Args:
            field: Field name
            pattern: Regex pattern
            options: Regex options (i=case-insensitive, etc.)
        """
        self.filter[field] = {"$regex": pattern, "$options": options}
        return self

    def filter_date_range(self, field: str, start: datetime, end: datetime) -> "QueryBuilder":
        """Add date range filter.
        
        Args:
            field: Field name (should be datetime field)
            start: Start date
            end: End date
        """
        self.filter[field] = {"$gte": start, "$lte": end}
        return self

    def sort_by(self, field: str, order: SortOrder = SortOrder.ASC) -> "QueryBuilder":
        """Add sort criterion.
        
        Args:
            field: Field name
            order: Sort order (ASC or DESC)
        """
        self.sort.append((field, order.value))
        return self

    def sort_asc(self, field: str) -> "QueryBuilder":
        """Sort by field ascending."""
        return self.sort_by(field, SortOrder.ASC)

    def sort_desc(self, field: str) -> "QueryBuilder":
        """Sort by field descending."""
        return self.sort_by(field, SortOrder.DESC)

    def paginate(self, page: int = 1, page_size: int = 20) -> "QueryBuilder":
        """Add pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
        """
        self.skip_count = (page - 1) * page_size
        self.limit_count = page_size
        return self

    def limit(self, count: int) -> "QueryBuilder":
        """Set result limit."""
        self.limit_count = count
        return self

    def skip(self, count: int) -> "QueryBuilder":
        """Set skip count."""
        self.skip_count = count
        return self

    def build(self) -> tuple[dict, list[tuple[str, int]], int, int]:
        """Build query components.
        
        Returns:
            Tuple of (filter, sort, skip, limit)
        """
        return self.filter, self.sort, self.skip_count, self.limit_count

    def to_dict(self) -> dict:
        """Export as dictionary for inspection."""
        return {
            "filter": self.filter,
            "sort": self.sort,
            "skip": self.skip_count,
            "limit": self.limit_count,
        }


class PaginationParams:
    """Pagination parameters"""

    def __init__(self, page: int = 1, page_size: int = 20, max_page_size: int = 100):
        self.page = max(1, page)  # Ensure page >= 1
        self.page_size = min(page_size, max_page_size)  # Enforce max
        self.skip = (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse:
    """Generic paginated response"""

    def __init__(self, data: list, total: int, page: int, page_size: int):
        self.data = data
        self.total = total
        self.page = page
        self.page_size = page_size
        self.pages = (total + page_size - 1) // page_size  # Ceiling division

    def to_dict(self) -> dict:
        return {
            "data": self.data,
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total": self.total,
                "pages": self.pages,
            },
        }
