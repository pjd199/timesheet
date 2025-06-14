"""Utility functions."""

from typing import Any, TypeVar

_T = TypeVar("_T")


def include_from_dict(cls: type[_T]) -> type[_T]:
    """A decorator that adds a 'from_dict' class method to a dataclass."""

    @classmethod
    def from_dict(cls: type[_T], data: dict[str, Any]) -> _T:
        """Creates an instance of the dataclass from a dictionary."""
        field_names = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)

    cls.from_dict = from_dict
    return cls
