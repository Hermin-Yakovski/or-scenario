# or_scenario/scenario.py
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from dal import DataHandler


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


class Scenario:
    """Template framework for Operations Research workflows.

    This class will be fully implemented in Task 5.
    """
    pass
