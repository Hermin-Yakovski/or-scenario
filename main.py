from typing import Any, Hashable, Optional, Tuple, Type

from register import Dimension, Register, Parameter
from or_algo import Algorithm
from dal import DataHandler


class Scenario(object):
    _version_id: Hashable
    _algorithm: Optional[Algorithm]
    _data: Register[Parameter]
    _load_steps: List[LoadStep]


    def __init__(self, version_id: Hashable):
        self._version_id = version_id
        self._algorithm = None
        self._data = Register[Parameter]()
        self._load_steps = []

    def get(self, param: Parameter, dim: Tuple[Dimension, ...], ix: Tuple[int, ...]) -> Any:
        pass

    def set(self, param: Parameter, dim: Tuple[Dimension, ...], ix: Tuple[int, ...], value: Any) -> None:
        pass

    def set_algorithm(self, algo: Type[Algorithm], *args, **kwargs) -> None:
        pass

    def exec_algorithm(self) -> None:
        pass

    def load(self):
        for step in self._load_steps:
            step.run()


    def validate(self):
        pass


class LoadStep(object):
    def __init__(self, handler: DataHandler, mapping: Callable,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
    ) -> None:
        pass

    def run(self):
        pass


if __name__ == '__main__':
    scn = Scenario(1)