from enum import Enum

class QueryExecutionStage(Enum):
    BGP = "BGP"
    FILTER = "Filter"
    UNION = "Union"
    ORDER_BY = "OrderBy"
    SLICE = "Slice"
    GROUP = "Group"
    AGGREGATE = "AggregateJoin"
    DISTINCT = "Distinct"
    OPTIONAL = "LeftJoin"
    MINUS = "Minus"
    PROJECT = "Project"
    EXTEND = "Extend"
    TO_MULTISET = "ToMultiSet"
    REDUCED = "Reduced"
    JOIN = "Join"
    GRAPH = "Graph"

class QueryType(Enum):
    SELECT = "SelectQuery"
    ASK = "AskQuery"
    CONSTRUCT = "ConstructQuery"
    DESCRIBE = "DescribeQuery"
    GRAPH = "ServiceGraphPattern"