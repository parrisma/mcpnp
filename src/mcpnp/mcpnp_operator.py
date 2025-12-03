from enum import Enum

class McpNpOperator(Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    DIVIDE = "divide"
    MULTIPLY = "multiply"

    def __str__(self):
        return self.value