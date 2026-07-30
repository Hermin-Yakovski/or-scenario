# or_scenario/scenario.py
from __future__ import annotations

import builtins
import logging
from typing import TYPE_CHECKING, Any, get_args, get_origin

import pandas as pd
from or_register import (
    Dimension,
    DimensionError,
    Id,
    Index,
    Metric,
    Register,
    ValidationError,
)

from .orm import generate_fact_table, generate_sol_table
from .schema import BaseRequest

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable, Iterable
    from pathlib import Path

    from data_access_layer import DataHandler
    from or_algo import Algorithm
    from or_register import RegisterKey
    from sqlalchemy.orm import Session

    from .schema import BaseResponse

logger = logging.getLogger("or_scenario")


class Scenario:
    """Base class for domain-specific OR scenarios."""

    _version_id: Hashable
    _algorithm: Algorithm | None
    _data: Register[Any]
    _request: BaseRequest | None

    def __init__(self, request: BaseRequest | None = None) -> None:
        self._request = request or BaseRequest()
        self._version_id = self._request.request_id
        self._algorithm = None
        self._data = Register()

    @staticmethod
    def _load_step(
        handler: DataHandler,
        path: Path,
        table: str,
        *,
        cols: Iterable[str] | None = None,
        filter_: Callable[[dict[str, Any]], bool] | None = None,
        limit: int | None = None,
        strict: bool = True,
    ) -> Callable[[Callable[[Scenario, list[dict[str, Any]]], None]], Callable[..., None]]:
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

        def decorator(
            mapping: Callable[[Scenario, list[dict[str, Any]]], None],
        ) -> Callable[..., None]:
            def wrapper(self: Scenario, **kwargs: Any) -> None:
                try:
                    records = handler.fetch(
                        path=path,
                        table=table,
                        cols=cols,
                        filter_=filter_,
                        limit=limit,
                        strict=strict,
                    )
                    mapping(self, records, **kwargs)
                except Exception:
                    if strict:
                        raise
                    # TODO: Log error and continue

            return wrapper

        return decorator

    def get(self, param: RegisterKey, dim: tuple[Dimension, ...], ix: tuple[int, ...]) -> Any:
        """Get a value from the scenario data.

        Args:
            param: The parameter to retrieve
            dim: The dimension tuple
            ix: The index tuple

        Returns:
            The value at the specified location
        """
        return self._data[param][dim][ix]

    def set(
        self, param: RegisterKey, dim: tuple[Dimension, ...], ix: tuple[int, ...], value: Any
    ) -> None:
        """Set a value in the scenario data.

        Args:
            param: The parameter to set
            dim: The dimension tuple
            ix: The index tuple
            value: The value to set
        """
        self._data[param][dim][ix] = value

    def set_algorithm(self, algo: type[Algorithm], *args: Any, **kwargs: Any) -> None:
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

    def load(self, session: Session | None = None) -> None:
        """Load scenario data from database or files.

        Args:
            session: Optional SQLAlchemy session with active transaction.
                     If provided, subclasses should load from database.
                     If None, subclasses should load from files.

        Raises:
            NotImplementedError: Subclass must override
        """
        raise NotImplementedError("Subclasses must implement load()")

    def dump(
        self,
        session: Session,
        params: builtins.set[RegisterKey],
        dimension: tuple[Dimension, ...],
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
        identifier: str = "snapshot_id" if fact else "version_id"

        # Generate the Sol table class dynamically
        dimension_names = [dim.name for dim in dimension]
        table = (
            generate_fact_table(*dimension_names) if fact else generate_sol_table(*dimension_names)
        )

        # Delete existing records with this version_id using ORM
        session.query(table).filter(getattr(table, identifier) == self._version_id).delete()

        # Collect all records to insert
        records = []
        for param in params:
            if param not in self._data:
                continue
            index_space = self._data[param][dimension]
            if not len(index_space):
                continue
            for index in index_space.keys():  # noqa: SIM118
                row = {
                    "parameter_id": param.id,
                    identifier: self._version_id,
                    "quantity": index_space[index],
                }
                for i, dim in enumerate(dimension):
                    row[f"{dim.name.lower()}_id"] = index[i]
                records.append(table(**row))

        if records:
            session.add_all(records)

    def validate(self, param: RegisterKey = Id) -> None:
        """Validate scenario data.

        Validates all parameters in self._data against the reference dimension
        from the specified parameter (defaults to Id).

        Args:
            param: The parameter whose dimension serves as reference for validation
                   (defaults to Id)

        Raises:
            DimensionError: If index length mismatch or invalid index reference
            ValidationError: If value doesn't match expected vtype
        """
        dim = self._data[param]

        for key in self._data:
            for dimension in self._data[key]:
                for index in self._data[key][dimension].keys():  # noqa: SIM118
                    # Validate index length matches dimension length
                    if len(dimension) != len(index):
                        msg = (
                            f"[v{key.id}] {key}{dimension}{index}: "
                            f"dimension length {len(dimension)} does not match index length {len(index)}"
                        )
                        raise DimensionError(msg)

                    # Validate index exists in reference dimension
                    for d, ix in zip(dimension, index):
                        if not ((ix,) in dim[d,] or (d is Metric) or d == Index):
                            msg = (
                                f"[v{key.id}] {key}{dimension}{index}: "
                                f"index {ix} does not match any index of dimension {d.name}"
                            )
                            raise DimensionError(msg)

                    value = self._data[key][dimension][index]
                    if key.vtype is None or key.vtype == Any:
                        pass

                    elif get_origin(key.vtype) in [list, set, tuple]:
                        # Validate iterable type
                        origin = get_origin(key.vtype)
                        if origin is not None and not isinstance(value, origin):
                            msg = (
                                f"[v{key.id}] {key}{dimension}{index}: "
                                f"expected {origin}, got {type(value)}, value={value}"
                            )
                            raise ValidationError(msg)

                        arg = get_args(key.vtype)[0]
                        if get_args(arg):
                            arg = get_args(arg)[0]

                        for v in value:
                            if isinstance(arg, Dimension):
                                if (v,) not in dim[arg,]:  # type: ignore[operator]
                                    msg = (
                                        f"[v{key.id}] {key}{dimension}{index}: "
                                        f"value {v} does not match any index of dimension {arg.name}"
                                    )
                                    raise ValidationError(msg)
                            elif not isinstance(v, arg):
                                msg = (
                                    f"[v{key.id}] {key}{dimension}{index}: "
                                    f"{get_origin(key.vtype)} expected elements of {arg}, "
                                    f"got {type(v)}, value={v}"
                                )
                                raise ValidationError(msg)

                    elif isinstance(key.vtype, Dimension):
                        if (value,) not in dim[key.vtype,]:  # type: ignore[operator]
                            msg = (
                                f"[v{key.id}] {key}{dimension}{index}: "
                                f"value {value} does not match any index of dimension {key.vtype.name}"
                            )
                            raise ValidationError(msg)

                    elif not isinstance(value, key.vtype):
                        msg = (
                            f"[v{key.id}] {key}{dimension}{index}: "
                            f"expected {key.vtype}, got {type(value)}, value={value}"
                        )
                        raise ValidationError(msg)

    def as_frames(self, display_cn: bool = False) -> dict[tuple[Dimension, ...], pd.DataFrame]:
        """Convert scenario data to pandas DataFrames.

        Args:
            display_cn: If True, use Chinese names; otherwise use English names

        Returns:
            Dictionary mapping dimension tuples to DataFrames. Each DataFrame has
            columns for each dimension followed by columns for each parameter.
        """
        frames: dict[tuple[Dimension, ...], pd.DataFrame] = {}
        rows: dict[tuple[Dimension, ...], dict[tuple[int, ...], list[Any]]] = {}
        columns: dict[tuple[Dimension, ...], list[str]] = {}

        for key in self._data:
            col: str = key.name_cn if display_cn else key.name
            for dimension in self._data[key]:
                if dimension not in rows:
                    rows[dimension] = {}
                    columns[dimension] = []
                if col not in columns[dimension]:
                    for index in rows[dimension]:
                        rows[dimension][index].append(None)
                    columns[dimension].append(col)
                index_space = self._data[key][dimension]
                for index in index_space.keys():  # noqa: SIM118
                    value = index_space[index]
                    if index not in rows[dimension]:
                        rows[dimension][index] = [None for _ in columns[dimension]]
                    rows[dimension][index][-1] = value

        for dimension, col_list in columns.items():
            dataframe_columns: list[str] = [
                d.name_cn if display_cn else d.name for d in dimension
            ] + col_list
            dataframe_rows: list[list[Any]] = []
            for index in rows[dimension]:
                dataframe_rows.append([i for i in index] + rows[dimension][index])
            frames[dimension] = pd.DataFrame(dataframe_rows, columns=dataframe_columns)

        return frames

    def save_xlsx(self, path: Path, display_cn: bool = False) -> None:
        """Export scenario data to Excel file.

        Creates an Excel file with one sheet per dimension combination.
        Each sheet contains data for all parameters across that dimension.

        Args:
            path: Directory where Excel file will be saved
            display_cn: If True, use Chinese names; otherwise use English names
        """
        frames = self.as_frames(display_cn)

        with pd.ExcelWriter(
            path / f"{type(self).__name__}_version_{self._version_id}.xlsx", engine="openpyxl"
        ) as writer:
            if not frames:
                # Handle empty scenario - create empty sheet
                pd.DataFrame().to_excel(writer, sheet_name="empty", index=False)
            else:
                # Create one sheet per dimension combination
                for dimension, df in frames.items():
                    sheet_name = "_".join(d.name_cn if display_cn else d.name for d in dimension)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

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
        return bool(identifier) and all(c.isalnum() or c == "_" for c in identifier)

    def _get_sol_table_name(self, dimension: tuple[Dimension, ...]) -> str:
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
            raise ValueError(
                f"Invalid table name '{table_name}': dimension names must be alphanumeric"
            )
        return table_name
