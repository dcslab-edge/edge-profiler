# coding: UTF-8

from typing import Any, Generator, Optional, Tuple


class TegraEvent:
    def __init__(self, event: str, alias: Optional[str] = None):
        self._event: str = event
        self._alias: str = alias if alias is not None else event

    @property
    def event(self) -> str:
        return self._event

    @property
    def alias(self) -> str:
        return self._alias


class TegraConfig:
    def __init__(self, interval: int, events: Tuple[TegraEvent, ...]):
        self._interval: int = interval
        self._events: Tuple[TegraEvent, ...] = events

    @property
    def interval(self) -> int:
        return self._interval

    @property
    def events(self) -> Tuple[TegraEvent, ...]:
        return self._events

    @property
    def event_names(self) -> Generator[str, Any, None]:
        return (event.alias for event in self._events)

    @property
    def event_str(self) -> str:
        return ','.join(event.event for event in self._events)

    def merge_events(self, new_events: Tuple[TegraEvent, ...]) -> 'TegraConfig':
        return TegraConfig(self._interval, self._events + new_events)
