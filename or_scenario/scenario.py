# or_scenario/scenario.py
from pathlib import Path
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Tuple, Type
from datetime import datetime

from dal import DataHandler
from or_algo import Algorithm
from register import Dimension, Id, Parameter, Register
from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    """Base request with common fields."""
    request_id: int = Field(default_factory=lambda: int(datetime.now().strftime("%y%m%d%H%M%S%f")[:-4]),
                            description="identity of the data")


class BaseResponse(BaseModel):
    """Base response with common fields."""
    request_id: int = Field(..., description="identity of the data")
    status: int = Field(..., description="status of the service")
    message: str = Field(default="Default message", description="message of the service")
    timestamp: datetime = Field(default_factory=datetime.now, description="timestamp of the data")
    response: Any = Field(default=None, description="response of the data")


class LoadStep:
    """Encapsulates a single data loading operation."""

    def __init__(
        self,
        handler: DataHandler,
        mapping: Callable[[List[Dict[str, Any]]], None],
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
    ) -> None:
        self.handler = handler
        self.mapping = mapping
        self.path = path
        self.table = table
        self.cols = cols
        self.filter_ = filter_
        self.limit = limit
        self.strict = strict

    def run(self) -> None:
        """Fetch data via handler and call mapping function."""
        records = self.handler.fetch(
            path=self.path,
            table=self.table,
            cols=self.cols,
            filter_=self.filter_,
            limit=self.limit,
            strict=self.strict
        )
        self.mapping(records)


class Scenario:
    """Base class for domain-specific OR scenarios."""

    _version_id: Hashable
    _algorithm: Optional[Algorithm]
    _data: Register[Parameter]
    _load_steps: List[LoadStep]
    _request: Optional[BaseRequest]

    def __init__(self, version_id: Hashable) -> None:
        self._version_id = version_id
        self._algorithm = None
        self._data = Register[Parameter]()
        self._load_steps = []
        self._request = None

    def get(self, param: Parameter, dim: Tuple[Dimension, ...], ix: Tuple[int, ...]) -> Any:
        """Get a value from the scenario data.

        Args:
            param: The parameter to retrieve
            dim: The dimension tuple
            ix: The index tuple

        Returns:
            The value at the specified location
        """
        return self._data[param][dim][ix]

    def set(self, param: Parameter, dim: Tuple[Dimension, ...], ix: Tuple[int, ...], value: Any) -> None:
        """Set a value in the scenario data.

        Args:
            param: The parameter to set
            dim: The dimension tuple
            ix: The index tuple
            value: The value to set
        """
        self._data[param][dim][ix] = value

    def set_algorithm(self, algo: Type[Algorithm], *args: Any, **kwargs: Any) -> None:
        """Set the algorithm for this scenario.

        Args:
            algo: The Algorithm class to instantiate
            *args: Positional arguments to pass to the algorithm
            **kwargs: Keyword arguments to pass to the algorithm
        """
        self._algorithm = algo(*args, **kwargs)

    def exec_algorithm(self) -> None:
        """Execute the algorithm on this scenario's data.

        Raises:
            RuntimeError: If no algorithm has been set
        """
        if self._algorithm is None:
            raise RuntimeError("Algorithm not set. Call set_algorithm() first.")
        self._algorithm.solve(self._data)

    def load(self) -> None:
        """Execute all load steps to populate scenario data."""
        for step in self._load_steps:
            step.run()

    def validate(self, param: Parameter = Id) -> None:
        """Validate scenario data.

        Args:
            param: The parameter to validate (defaults to Id)
        """
        dim = self._data[param]
        self._data.validate(dim, raise_errors=True)

    def response(self, *args: Any, **kwargs: Any) -> BaseResponse:
        """Package results into BaseResponse. Subclasses must implement."""
        raise NotImplementedError("Subclasses must implement response()")
