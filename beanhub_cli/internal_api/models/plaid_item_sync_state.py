from enum import Enum


class PlaidItemSyncState(str, Enum):
    IMPORT_COMPLETE = "IMPORT_COMPLETE"
    IMPORT_COMPLETE_NO_CHANGES = "IMPORT_COMPLETE_NO_CHANGES"
    IMPORT_FAILED = "IMPORT_FAILED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SYNC_COMPLETE = "SYNC_COMPLETE"
    SYNC_FAILED = "SYNC_FAILED"

    def __str__(self) -> str:
        return str(self.value)
