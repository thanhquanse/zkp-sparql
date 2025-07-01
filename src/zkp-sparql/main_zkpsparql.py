import os
import sys
import rdflib
from contextlib import redirect_stdout
from memory_profiler import profile
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.superhandler import ZKPSuperHandler
from utils.measure import timeit

LOG_FILE = "./logs/main_zkpsparql_experiment.log"
fp = open(LOG_FILE, "w+")

class TeeLog:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, message):
        for s in self.streams:
            s.write(f"{message}\n")
            s.flush()
    def flush(self):
        for s in self.streams:
            s.flush()

def log_and_write(message: str, logfile: str = LOG_FILE):
    print(f"{message}\n")
    with open(logfile, "a") as file:
        file.write(f"{message}\n")

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

@timeit
@profile
def performSPARQL(graph: Graph, query: str):
    return graph.query(query)

@timeit
@profile
def performZKP(graph: Graph, query: str, params: dict):
    stage_extracter = StageExtracter()
    rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval
    results = performSPARQL(graph, query)
    ZKPSuperHandler(stage_extracter.get_stage_vals(), params).build(log_path=LOG_FILE)

@timeit
@profile
def zkpFunc(dataset_query_dict: dict):
    params: dict = {
        "k": 20,
        "paramgen": True,
        "param": f"./proof/param_20.bin",
        "proofgen": True,
        "step_num": 150000,
    }
    for dataset in dataset_query_dict.keys():
        path = dataset_query_dict[dataset]["path"]
        graph: Graph = load_dataset(path)
        queries: list[str] = dataset_query_dict[dataset]["queries"]

        for query_str in queries:
            print(f"----- Experimenting {query_str} -----")
            query_name = os.path.basename(query_str).split('.')[0]
            query: str = load_query(query_str)
            params["proof"] = f"./proof/super_proof_{dataset}_{query_name}"
            # with open(LOG_FILE, "a") as file:
            #     logtee = TeeLog(sys.stdout, file)
            #     with redirect_stdout(logtee):
            performZKP(graph, query, params)

if __name__ == "__main__":
    dataset_query_dict = {
        "swdf": {
            "path": "./datasets/swdf/swdf_light.nt",
            "queries": [
                "./datasets/swdf/benchmark_queries/q1_select.sparql",
                "./datasets/swdf/benchmark_queries/q2_select.sparql",
                "./datasets/swdf/benchmark_queries/q3_select.sparql",
                "./datasets/swdf/benchmark_queries/q4_select.sparql",
                "./datasets/swdf/benchmark_queries/q5_select.sparql",
            ]
        },
        "drugbank": {
            "path": "./datasets/drugbank/drugbank.nt",
            "queries": [
                "./datasets/drugbank/benchmark_queries/q1_select.sparql",
                "./datasets/drugbank/benchmark_queries/q2_select.sparql",
                "./datasets/drugbank/benchmark_queries/q3_select.sparql",
                "./datasets/drugbank/benchmark_queries/q4_select.sparql",
                "./datasets/drugbank/benchmark_queries/q5_select.sparql",
            ]
        },
        "bsbm": {
            "path": "./datasets/bsbm/bsbm.nt",
            "queries": [
                "./datasets/bsbm/benchmark_queries/q1_select.sparql",
                "./datasets/bsbm/benchmark_queries/q2_select.sparql",
                "./datasets/bsbm/benchmark_queries/q3_select.sparql",
                "./datasets/bsbm/benchmark_queries/q4_select.sparql",
                "./datasets/bsbm/benchmark_queries/q5_select.sparql",
            ]
        }
    }
    zkpFunc(dataset_query_dict)