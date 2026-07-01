"""Execution retry policy."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class RetryPolicy:
    """Handle transient execution failures with exponential backoff."""

    RETRYABLE_CODES = {
        10004,
        10008,
        10016,
    }
    NON_RETRYABLE_CODES = {
        10006,
        10014,
        10019,
    }

    def __init__(self, max_attempts: int = 3, base_delay_seconds: float = 0.5) -> None:
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds

    def execute(self, operation: Callable[[], T], get_error_code: Callable[[T], int | None]) -> T:
        last_result = operation()
        code = get_error_code(last_result)
        attempt = 1
        while code in self.RETRYABLE_CODES and attempt < self.max_attempts:
            time.sleep(self.base_delay_seconds * (2 ** (attempt - 1)))
            last_result = operation()
            code = get_error_code(last_result)
            attempt += 1
        return last_result
