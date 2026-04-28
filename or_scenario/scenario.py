# or_scenario/scenario.py
from pathlib import Path
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Tuple

from dal import DataHandler
from or_algo import Algorithm
from register import Dimension, Parameter, Register


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

    def __init__(self, version_id: Hashable) -> None:
        self._version_id = version_id
        self._algorithm = None
        self._data = Register[Parameter]()
        self._load_steps = []
