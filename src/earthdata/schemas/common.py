"""Shared API schemas: pagination envelope and sort ordering."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, computed_field


class SortOrder(StrEnum):
    """Sort direction for list endpoints."""

    ASC = "asc"
    DESC = "desc"


class Page[ItemT: BaseModel](BaseModel):
    """A paginated collection of items with pagination metadata."""

    items: list[ItemT]
    total: int = Field(description="Total number of records matching the filters.")
    limit: int = Field(description="Maximum number of records returned per page.")
    offset: int = Field(description="Number of records skipped before this page.")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_more(self) -> bool:
        """Whether more records exist beyond this page."""
        return self.offset + len(self.items) < self.total
