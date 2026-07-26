from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    name: str
    passed: bool
    summary: str
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    recommendation: str | None = None