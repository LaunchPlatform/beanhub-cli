from enum import Enum


class RepositoryType(str, Enum):
    CONNECT = "CONNECT"
    GIT = "GIT"

    def __str__(self) -> str:
        return str(self.value)
