"""Asserts reutilizables para contratos de salida compatibles con JSON."""

from __future__ import annotations

import unittest
from dataclasses import is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any


def assert_json_contract(
    test: unittest.TestCase,
    value: Any,
    *,
    forbidden_types: tuple[type[Any], ...] = (),
    path: str = "root",
) -> None:
    """Exige tipos JSON exactos y rechaza cualquier objeto de implementación.

    La comparación por identidad es intencionada: ni siquiera las subclases de
    los tipos admitidos forman parte del contrato de transporte.
    """
    if forbidden_types:
        test.assertNotIsInstance(value, forbidden_types, f"objeto interno en {path}")

    if isinstance(value, Enum):
        test.fail(f"enum no JSON en {path}: {type(value).__name__}")
    if type(value) in (tuple, set, frozenset, MappingProxyType):
        test.fail(f"colección no JSON en {path}: {type(value).__name__}")
    if is_dataclass(value) and not isinstance(value, type):
        test.fail(f"dataclass interna en {path}: {type(value).__name__}")
    if callable(value):
        test.fail(f"callable no JSON en {path}: {type(value).__name__}")
    if isinstance(value, BaseException):
        test.fail(f"excepción no JSON en {path}: {type(value).__name__}")

    value_type = type(value)
    if value_type in (str, int, float, bool, type(None)):
        return
    if value_type is list:
        for index, item in enumerate(value):
            assert_json_contract(
                test,
                item,
                forbidden_types=forbidden_types,
                path=f"{path}[{index}]",
            )
        return
    if value_type is dict:
        for key, item in value.items():
            test.assertIs(type(key), str, f"clave no JSON en {path}: {key!r}")
            assert_json_contract(
                test,
                item,
                forbidden_types=forbidden_types,
                path=f"{path}.{key}",
            )
        return
    test.fail(f"tipo no JSON en {path}: {value_type.__name__}")
