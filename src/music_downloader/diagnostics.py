"""Consistent diagnostics at service isolation boundaries."""

from __future__ import annotations


def exception_diagnostic(error: Exception) -> str:
    message = str(error).strip() or "sem mensagem"
    return f"{type(error).__name__}: {message}"
