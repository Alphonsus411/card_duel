from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from functools import lru_cache
from collections.abc import Callable
from types import ModuleType
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from ..domain import enums as enum_module
from ..domain import models as model_module
from ..engine.commands import EXECUTABLE_COMMAND_TYPES
from ..rules.config import RuleSet


def _registry(module: ModuleType, predicate: Callable[[type], bool]) -> dict[str, type]:
    return {
        name: value
        for name, value in vars(module).items()
        if isinstance(value, type) and predicate(value)
    }


_ENUM_TYPES = _registry(
    enum_module, lambda value: issubclass(value, Enum) and value is not Enum
)
_DATACLASS_TYPES = {
    **_registry(model_module, is_dataclass),
    **{command_type.__name__: command_type for command_type in EXECUTABLE_COMMAND_TYPES},
    "RuleSet": RuleSet,
}


@lru_cache(maxsize=None)
def _type_hints(cls: type) -> dict[str, Any]:
    return get_type_hints(cls)


def _matches_type(value: Any, annotation: Any) -> bool:
    if annotation is Any:
        return True
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in {Union, UnionType}:
        return any(_matches_type(value, item) for item in args)
    if origin is tuple:
        if not isinstance(value, tuple):
            return False
        if len(args) == 2 and args[1] is Ellipsis:
            return all(_matches_type(item, args[0]) for item in value)
        return len(value) == len(args) and all(
            _matches_type(item, expected) for item, expected in zip(value, args, strict=True)
        )
    if origin in {list, set, frozenset}:
        return isinstance(value, origin) and all(
            _matches_type(item, args[0]) for item in value
        )
    if origin is dict:
        return isinstance(value, dict) and all(
            _matches_type(key, args[0]) and _matches_type(item, args[1])
            for key, item in value.items()
        )
    if annotation is int:
        return type(value) is int
    if annotation in {str, bool, float}:
        return type(value) is annotation
    if annotation is type(None):
        return value is None
    if isinstance(annotation, type):
        return isinstance(value, annotation)
    return False


def _sort_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def encode_value(value: Any) -> Any:
    """Convierte únicamente tipos del dominio permitidos a estructuras JSON."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return {"$enum": type(value).__name__, "name": value.name}
    if is_dataclass(value) and not isinstance(value, type):
        type_name = type(value).__name__
        if type_name not in _DATACLASS_TYPES or _DATACLASS_TYPES[type_name] is not type(value):
            raise TypeError(f"Dataclass no autorizada para persistencia: {type_name}")
        return {
            "$type": type_name,
            "fields": {
                field.name: encode_value(getattr(value, field.name))
                for field in fields(value)
            },
        }
    if isinstance(value, tuple):
        return {"$tuple": [encode_value(item) for item in value]}
    if isinstance(value, frozenset):
        encoded = [encode_value(item) for item in value]
        return {"$frozenset": sorted(encoded, key=_sort_key)}
    if isinstance(value, set):
        encoded = [encode_value(item) for item in value]
        return {"$set": sorted(encoded, key=_sort_key)}
    if isinstance(value, list):
        return [encode_value(item) for item in value]
    if isinstance(value, dict):
        entries = [
            [encode_value(key), encode_value(item)] for key, item in value.items()
        ]
        return {"$mapping": entries}
    raise TypeError(f"Tipo no autorizado para persistencia: {type(value).__name__}")


def decode_value(value: Any) -> Any:
    """Restaura datos sin importar módulos ni ejecutar tipos indicados por el archivo."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [decode_value(item) for item in value]
    if not isinstance(value, dict):
        raise ValueError("La estructura persistida contiene un valor no válido")
    if "$enum" in value:
        if set(value) != {"$enum", "name"}:
            raise ValueError("Representación de enum no válida")
        enum_type = _ENUM_TYPES.get(value["$enum"])
        if enum_type is None:
            raise ValueError(f"Enum no autorizado: {value['$enum']}")
        try:
            return getattr(enum_type, value["name"])
        except KeyError as exc:
            raise ValueError("Miembro de enum desconocido") from exc
    if "$type" in value:
        if set(value) != {"$type", "fields"} or not isinstance(value["fields"], dict):
            raise ValueError("Representación de dataclass no válida")
        cls = _DATACLASS_TYPES.get(value["$type"])
        if cls is None:
            raise ValueError(f"Tipo no autorizado: {value['$type']}")
        class_fields = {field.name: field for field in fields(cls)}
        expected = set(class_fields)
        supplied = set(value["fields"])
        compatible_missing = (
            {"ability_source_profile"} if cls is model_module.StackItem else set()
        )
        if cls is model_module.AbilitySourceProfile:
            compatible_missing.add("nature_is_certain")
        if cls is model_module.EffectDefinition:
            compatible_missing.update(
                {"failure_destination_zone", "exhaustion_policy"}
            )
        missing_required = (expected - supplied) - compatible_missing
        if missing_required or supplied - expected:
            raise ValueError(
                f"Campos incompatibles para {value['$type']}: "
                f"faltan={sorted(missing_required)}, sobran={sorted(supplied - expected)}"
            )
        decoded = {
            name: decode_value(item) for name, item in value["fields"].items()
        }
        hints = _type_hints(cls)
        invalid = [
            name
            for name, item in decoded.items()
            if name in hints and not _matches_type(item, hints[name])
        ]
        if invalid:
            raise ValueError(
                f"Tipos de campo incompatibles para {value['$type']}: {sorted(invalid)}"
            )
        return cls(**decoded)
    tagged = [key for key in ("$tuple", "$frozenset", "$set", "$mapping") if key in value]
    if len(tagged) != 1 or len(value) != 1:
        raise ValueError("Contenedor persistido no válido")
    tag = tagged[0]
    payload = value[tag]
    if tag == "$tuple":
        return tuple(decode_value(item) for item in payload)
    if tag == "$frozenset":
        return frozenset(decode_value(item) for item in payload)
    if tag == "$set":
        return set(decode_value(item) for item in payload)
    if not isinstance(payload, list):
        raise ValueError("Mapeo persistido no válido")
    result = {}
    for entry in payload:
        if not isinstance(entry, list) or len(entry) != 2:
            raise ValueError("Entrada de mapeo no válida")
        key = decode_value(entry[0])
        if key in result:
            raise ValueError("Clave duplicada en mapeo persistido")
        result[key] = decode_value(entry[1])
    return result


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
