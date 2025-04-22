from enum import Enum

class AggregateOperations(Enum):
    COUNT = "Aggregate_Count"
    SUM = "Aggregate_Sum"
    AVG = "Aggregate_Avg"
    MAX = "Aggregate_Max"
    MIN = "Aggregate_Min"
    SAMPLE = "Aggregate_Sample"

class ExpressionEnum(Enum):
    MULTIPLICATIVE = "MultiplicativeExpression"
    ADDITIVE = "AdditiveExpression"