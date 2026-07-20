"""Thread-safe cooperative cancellation primitives."""

from __future__ import annotations

from threading import Event


class OperationCancelled(RuntimeError):
    """Raised inside a service operation when cancellation is requested."""


class CancellationToken:
    """A small wrapper around ``threading.Event`` shared by workers/services."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def wait(self, timeout: float) -> bool:
        """Wait for cancellation, returning true when it was requested."""

        return self._event.wait(timeout)

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise OperationCancelled("Operação cancelada pelo usuário.")
