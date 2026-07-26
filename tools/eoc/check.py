from abc import ABC, abstractmethod

from .result import CheckResult


class Check(ABC):

    NAME = "Unnamed"

    CRITICAL = True

    @abstractmethod
    def execute(self, context) -> CheckResult:
        ...