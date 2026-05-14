# or_scenario/schema.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    """Base request with common fields."""
    request_id: int = Field(
        default_factory=lambda: int(datetime.now().strftime("%y%m%d%H%M%S%f")[:-4]),
        description="identity of the data"
    )


class BaseResponse(BaseModel):
    """Base response with common fields."""
    request_id: int = Field(..., description="identity of the data")
    status: int = Field(..., description="status of the service")
    message: str = Field(default="Default message", description="message of the service")
    timestamp: datetime = Field(default_factory=datetime.now, description="timestamp of the data")
    response: Any = Field(default=None, description="response of the data")