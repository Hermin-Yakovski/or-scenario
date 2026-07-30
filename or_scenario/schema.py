# or_scenario/schema.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

_CST = timezone(timedelta(hours=8))
from typing import Any

from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    """Base request with common fields."""

    request_id: int = Field(
        default_factory=lambda: int(datetime.now(tz=_CST).strftime("%y%m%d%H%M%S%f")[:-4]),
        description="identity of the data",
    )


class BaseResponse(BaseModel):
    """Base response with common fields."""

    request_id: int = Field(..., description="identity of the data")
    status: int = Field(..., description="status of the service")
    message: str = Field(default="Default message", description="message of the service")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=_CST), description="timestamp of the data"
    )
    response: Any = Field(default=None, description="response of the data")
