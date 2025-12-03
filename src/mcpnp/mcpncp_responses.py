from enum import Enum

class McpNpResponses(Enum):
    RESULT = "result"
    STATUS = "status"
    OK = "ok"
    ERROR = "error"
    MESSAGE = "message"
    NAN = "nan"

    def __str__(self):
        return self.value
