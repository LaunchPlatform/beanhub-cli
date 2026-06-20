from enum import Enum


class SyncBatchState(str, Enum):
    IMPORTING = "IMPORTING"
    IMPORT_COMPLETE = "IMPORT_COMPLETE"
    IMPORT_COMPLETE_NO_CHANGES = "IMPORT_COMPLETE_NO_CHANGES"
    IMPORT_FAILED = "IMPORT_FAILED"
    SYNCING = "SYNCING"
    SYNC_COMPLETE = "SYNC_COMPLETE"

    def __str__(self) -> str:
        return str(self.value)
