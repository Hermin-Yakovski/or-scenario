"""or-scenario: Template framework for Operations Research workflows."""

# Re-export orm proxy for convenience
from . import orm
from .scenario import Scenario
from .schema import BaseRequest, BaseResponse

__all__ = ["BaseRequest", "BaseResponse", "Scenario", "orm"]
__version__ = "0.4.0"
