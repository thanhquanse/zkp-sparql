import os
from rdflib import Graph

def load_dataset(path: str) -> Graph:
    g = Graph()
    g.parse(path)
    print(f"Loaded graph {path} with size: {len(g)}")

    return g

def load_query(path: str) -> str:
    if not os.path.exists(path):
        print(f"Error: File {path} not found")
        exit(1)

    try:
        with open(path, "r") as file:
            sparql_query = file.read()
    except IOError as e:
        print(f"Error reading file {path}: {e}")
        exit(1)
    
    return sparql_query

def func(dataset_query_dict: dict):
    for dataset in dataset_query_dict.keys():
        path = dataset_query_dict[dataset]["path"]
        graph: Graph = load_dataset(path)
        queries: list[str] = dataset_query_dict[dataset]["queries"]

        for query_str in queries:
            print(f"----- Running {query_str} -----")
            query: str = load_query(query_str)

            results = graph.query(query)

            for rs in results:
                print(f"{rs}")

if __name__ == "__main__":
    dataset_query_dict = {
        "swdf": {
            "path": "./datasets/swdf/swdf_25_pct.nt",
            "queries": [
                "./datasets/swdf/benchmark_queries/q1_select.sparql",
                "./datasets/swdf/benchmark_queries/q2_select.sparql",
                "./datasets/swdf/benchmark_queries/q3_select.sparql",
                "./datasets/swdf/benchmark_queries/q4_ask.sparql",
                "./datasets/swdf/benchmark_queries/q5_select.sparql",
                "./datasets/swdf/single_gate_benchmark_queries/q1_filter.sparql"
            ]
        },
        "drugbank": {
            "path": "./datasets/drugbank/drugbank_25_pct.nt",
            "queries": [
                "./datasets/drugbank/benchmark_queries/q1_select.sparql",
                "./datasets/drugbank/benchmark_queries/q2_select.sparql",
                "./datasets/drugbank/benchmark_queries/q3_select.sparql",
                "./datasets/drugbank/benchmark_queries/q4_ask.sparql",
                "./datasets/drugbank/benchmark_queries/q5_select.sparql",
            ]
        },
        "bsbm": {
            "path": "./datasets/bsbm/bsbm_25_pct.nt",
            "queries": [
                "./datasets/bsbm/benchmark_queries/q1_select.sparql",
                "./datasets/bsbm/benchmark_queries/q2_select.sparql",
                "./datasets/bsbm/benchmark_queries/q3_select.sparql",
                "./datasets/bsbm/benchmark_queries/q4_ask.sparql",
                "./datasets/bsbm/benchmark_queries/q5_select.sparql",
            ]
        }
    }
    func(dataset_query_dict)