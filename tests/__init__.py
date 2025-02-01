"""Tests for gbp-fl"""

from functools import wraps
from typing import Any, Callable, TypeAlias, TypeVar
from unittest import TestCase

T = TypeVar("T", bound=TestCase)
TestFunc: TypeAlias = Callable[[T, *tuple[Any]], None]
Param: TypeAlias = list[Any]
Params: TypeAlias = list[Param]


def parametrized(lists_of_args: Params) -> Callable[[TestFunc[T]], TestFunc[T]]:
    """Turn TestCase test method into parametrized test"""

    def dec(func: TestFunc[T]) -> TestFunc[T]:
        @wraps(func)
        def wrapper(self: T, *args: Any, **kwargs: Any) -> None:
            for list_of_args in lists_of_args:
                name = ",".join(str(i) for i in list_of_args)
                with self.subTest(name):
                    func(self, *args, *list_of_args, **kwargs)

        return wrapper

    return dec
