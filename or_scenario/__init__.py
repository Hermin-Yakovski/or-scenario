"""or-scenario: Template framework for Operations Research workflows."""

from .schema import BaseRequest, BaseResponse
from .scenario import Scenario

# Re-export orm proxy for convenience
from . import orm  # type: ignore

__all__ = ["Scenario", "BaseRequest", "BaseResponse", "orm"]
__version__ = "0.2.0"
