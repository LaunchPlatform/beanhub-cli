from enum import Enum


class InboxDumpRequestState(str, Enum):
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"

    def __str__(self) -> str:
        return str(self.value)
