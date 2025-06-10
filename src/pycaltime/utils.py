from typing import Any, Dict, TypeVar, Type

_T = TypeVar('_T')

def include_from_dict(cls: Type[_T]) -> Type[_T]:
    """
    A decorator that adds a 'from_dict' class method to a dataclass.
    """
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> _T:
        """Creates an instance of the dataclass from a dictionary."""
        field_names = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)

    setattr(cls, 'from_dict', from_dict)
    return cls
