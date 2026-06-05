# or_scenario/scenario.py
from __future__ import annotations
from typing import TYPE_CHECKING

from register import Dimension, Id, Parameter, Register

from .orm import generate_sol_table, generate_fact_table
from .schema import BaseRequest

if TYPE_CHECKING:
    from pathlib import Path

    from data_access_layer import DataHandler
    from or_algo import Algorithm
    from sqlalchemy.orm import Session
    from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Set, Tuple, Type

    from .schema import BaseResponse


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

    def load(self, session: Optional[Session] = None) -> None:
        """Load scenario data from database or files.

        Args:
            session: Optional SQLAlchemy session with active transaction.
                     If provided, subclasses should load from database.
                     If None, subclasses should load from files.

        Raises:
            NotImplementedError: Subclass must override
        """
        raise NotImplementedError("Subclasses must implement load()")

    def dump(self,
        session: Session,
        params: Set[Parameter],
        dimension: Tuple[Dimension, ...],
        fact: bool = False,
    ) -> None:
        """Dump parameters to sol or fact table.

        Deletes all existing records with version_id/snapshot_id = self._version_id,
        then inserts new records from Register for given params/dimension.
        Skips params that don't exist in Register.

        Caller is responsible for transaction management.

        Args:
            session: SQLAlchemy session
            params: Set of parameters to dump
            dimension: Dimension tuple for table identification
            fact: If True, dump to fact table using snapshot_id column.
                  If False, dump to sol table using version_id column.

        """
        identifier: str = 'snapshot_id' if fact else 'version_id'

        # Generate the Sol table class dynamically
        dimension_names = [dim.name for dim in dimension]
        table =  generate_fact_table(*dimension_names) if fact else generate_sol_table(*dimension_names)

        # Delete existing records with this version_id using ORM
        session.query(table).filter(getattr(table, identifier) == self._version_id).delete()

        # Collect all records to insert
        records = []
        for param in params:
            for index in self._data.select(param, dimension):
                row = {
                    "parameter_id": param.id,
                    identifier: self._version_id,
                    "quantity": self._data[param][dimension][index],
                }
                for i, dim in enumerate(dimension):
                    row[f"{dim.name.lower()}_id"] = index[i]
                records.append(table(**row))

        if records:
            session.add_all(records)

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

    def _validate_sql_identifier(self, identifier: str) -> bool:
        """Validate that a string is a safe SQL identifier.

        Args:
            identifier: String to validate

        Returns:
            True if identifier is safe (alphanumeric and underscores only)
        """
        return bool(identifier) and all(c.isalnum() or c == '_' for c in identifier)

    def _get_sol_table_name(self, dimension: Tuple[Dimension, ...]) -> str:
        """Generate sol table name from dimension tuple.

        Table name follows convention: sol_{dim1}_{dim2}...
        Dimensions are sorted alphabetically for consistency.

        Args:
            dimension: Tuple of Dimension objects

        Returns:
            Sol table name (e.g., "sol_product_region")

        Raises:
            ValueError: If dimension name contains unsafe characters
        """
        sorted_dims = sorted(dimension, key=lambda d: d.name.lower())
        table_name = f"sol_{'_'.join(d.name.lower() for d in sorted_dims)}"
        if not self._validate_sql_identifier(table_name):
            raise ValueError(f"Invalid table name '{table_name}': dimension names must be alphanumeric")
        return table_name
