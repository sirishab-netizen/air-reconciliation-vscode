from dataclasses import dataclass, field
from datetime import datetime
from time import perf_counter


@dataclass
class TraceEvent:
    step: int
    event_type: str
    message: str
    timestamp: str
    duration_ms: float | None = None


@dataclass
class AgentTrace:
    events: list[TraceEvent] = field(default_factory=list)

    _timers: dict[str, float] = field(default_factory=dict)

    def add(
        self,
        event_type: str,
        message: str,
        duration_ms: float | None = None,
    ):
        self.events.append(
            TraceEvent(
                step=len(self.events) + 1,
                event_type=event_type,
                message=message,
                timestamp=datetime.now().isoformat(timespec="milliseconds"),
                duration_ms=duration_ms,
            )
        )

    def start_timer(self, name: str):
        self._timers[name] = perf_counter()

    def stop_timer(self, name: str) -> float:
        start = self._timers.pop(name, None)

        if start is None:
            return 0.0

        return (perf_counter() - start) * 1000

    def count(self, event_type: str) -> int:
        return sum(
            1 for event in self.events
            if event.event_type == event_type
        )

    def tool_call_count(self) -> int:
        return self.count("TOOL")

    def reasoning_count(self) -> int:
        return self.count("REASONING")

    def evidence_count(self) -> int:
        return self.count("EVIDENCE")

    def print(self):
        print("\nAGENT TRACE")
        print("-" * 80)

        for event in self.events:
            duration = (
                f" ({event.duration_ms:.1f} ms)"
                if event.duration_ms is not None
                else ""
            )

            print(
                f"{event.step}. "
                f"[{event.event_type}] "
                f"{event.message}"
                f"{duration}"
            )