"""or-scenario: Template framework for Operations Research workflows."""

from .schema import BaseRequest, BaseResponse
from .scenario import Scenario

__all__ = ["Scenario", "BaseRequest", "BaseResponse"]
__version__ = "0.1.0"
