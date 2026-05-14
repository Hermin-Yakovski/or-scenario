# or_scenario/scenario.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Tuple, Type, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from dal import DataHandler
from or_algo import Algorithm
from register import Dimension, Id, Parameter, Register  # type: ignore[import-untyped]
# pydantic imports removed - now in schema.py

from .schema import BaseRequest, BaseResponse


class Scenario:
    """Base class for domain-specific OR scenarios."""

    _version_id: Hashable
    _algorithm: Optional[Algorithm]
    _data: Register[Parameter]
    _request: Optional[BaseRequest]

    def __init__(self, request: Optional[BaseRequest] = None) -> None:
        self._request = request or BaseRequest()
        self._version_id = self._request.request_id
        self._algorithm = None
        self._data = Register[Parameter]()

    @staticmethod
    def _load_step(
        handler: DataHandler,
        path: Path,
        table: str,
        *,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True
    ) -> Callable[[Callable[[Scenario, List[Dict[str, Any]]], None]], Callable[..., None]]:
        """Decorator that wraps a method to auto-fetch data before calling mapping logic.

        The decorated method transforms from `mapping(self, records, **kwargs)` to
        `wrapper(self, **kwargs)` - the wrapper handles data fetching internally.

        Args:
            handler: DataHandler instance for fetching data
            path: Path to data directory
            table: Table/file name
            cols: Optional column filter
            filter_: Optional row filter function
            limit: Optional max records to fetch
            strict: If True, raise exceptions. If False, log and continue.

        Returns:
            Decorator function that transforms mapping methods
        """
        def decorator(mapping: Callable[[Scenario, List[Dict[str, Any]]], None]) -> Callable[..., None]:
            def wrapper(self: Scenario, **kwargs: Any) -> None:
                try:
                    records = handler.fetch(
                        path=path,
                        table=table,
                        cols=cols,
                        filter_=filter_,
                        limit=limit,
                        strict=strict
                    )
                    mapping(self, records, **kwargs)
                except Exception:
                    if strict:
                        raise
                    # TODO: Log error and continue
            return wrapper
        return decorator

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

    def load(self, session: Optional["Session"] = None) -> None:
        """Load scenario data from database or files.

        Args:
            session: Optional SQLAlchemy session with active transaction.
                     If provided, subclasses should load from database.
                     If None, subclasses should load from files.

        Raises:
            NotImplementedError: Subclass must override
        """
        raise NotImplementedError("Subclasses must implement load()")

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
