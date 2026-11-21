from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TagValue = Annotated[str, Field(min_length=1, max_length=32)]
TagList = Annotated[list[TagValue], Field(max_length=20)]


class Priority(StrEnum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TaskStatus(StrEnum):
    PENDING = "Pending"
    COMPLETED = "Completed"


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(max_length=5000)] = ""
    priority: Priority = Priority.MEDIUM
    tags: TagList = Field(default_factory=list)

    @field_validator("title", "description", mode="before")
    @classmethod
    def trim_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("tags", mode="before")
    @classmethod
    def trim_tags(cls, values: Any) -> Any:
        if isinstance(values, list):
            return [value.strip() if isinstance(value, str) else value for value in values]
        return values

    @field_validator("tags")
    @classmethod
    def deduplicate_tags(cls, values: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = value.casefold()
            if normalized not in seen:
                unique.append(value)
                seen.add(normalized)
        return unique


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    description: Annotated[str, Field(max_length=5000)] | None = None
    priority: Priority | None = None
    tags: TagList | None = None

    @field_validator("title", "description", mode="before")
    @classmethod
    def trim_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("tags", mode="before")
    @classmethod
    def trim_tags(cls, values: Any) -> Any:
        if isinstance(values, list):
            return [value.strip() if isinstance(value, str) else value for value in values]
        return values

    @field_validator("tags")
    @classmethod
    def deduplicate_tags(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        unique: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = value.casefold()
            if normalized not in seen:
                unique.append(value)
                seen.add(normalized)
        return unique

    @model_validator(mode="after")
    def require_editable_values(self) -> TaskUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one editable field is required")
        if any(getattr(self, name) is None for name in self.model_fields_set):
            raise ValueError("Editable fields cannot be null")
        return self


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: UUID
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(max_length=5000)]
    priority: Priority
    tags: TagList
    status: TaskStatus
    created_at: datetime = Field(alias="createdAt")

    @field_validator("title", "description", mode="before")
    @classmethod
    def trim_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("tags", mode="before")
    @classmethod
    def trim_tags(cls, values: Any) -> Any:
        if isinstance(values, list):
            return [value.strip() if isinstance(value, str) else value for value in values]
        return values

    @field_validator("created_at")
    @classmethod
    def require_utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("createdAt must be a UTC timestamp")
        return value.astimezone(UTC)


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    DATA_FILE_ERROR = "DATA_FILE_ERROR"
    NOT_FOUND = "NOT_FOUND"
    HTTP_ERROR = "HTTP_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    code: ErrorCode
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
