from enum import Enum


class DumpRequestState(str, Enum):
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"

    def __str__(self) -> str:
        return str(self.value)
