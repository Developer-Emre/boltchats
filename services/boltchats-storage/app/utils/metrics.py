import asyncio

import structlog

logger = structlog.get_logger()

_messages_consumed: int = 0
_messages_failed: int = 0


def record_consumed() -> None:
    global _messages_consumed
    _messages_consumed += 1


def record_failed() -> None:
    global _messages_failed
    _messages_failed += 1


def get_stats() -> dict[str, int]:
    return {
        "messages_consumed": _messages_consumed,
        "messages_failed": _messages_failed,
    }
