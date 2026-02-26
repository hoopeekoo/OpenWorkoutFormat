"""Visitor protocol and base transformer for AST traversal."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Visitor(Protocol):
    """Protocol for AST visitors."""

    def visit(self, node: Any) -> Any: ...


class BaseTransformer:
    """Base class for AST transformers that walk and optionally rewrite nodes."""

    def visit(self, node: Any) -> Any:
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node: Any) -> Any:
        return node
