import os
import sys
import rdflib
from contextlib import redirect_stdout
from memory_profiler import profile
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.superhandler import ZKPSuperHandler
from utils.measure import timeit

LOG_FILE = "./logs/experiment.log"
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
    log_and_write(f"Loaded graph {path} with size: {len(g)}")

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
@profile(stream=fp)
def performSPARQL(graph: Graph, query: str):
    return graph.query(query)

@timeit
@profile(stream=fp)
def performZKP(graph: Graph, query: str, params: dict):
    stage_extracter = StageExtracter()
    rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval
    results = performSPARQL(graph, query)
    ZKPSuperHandler(stage_extracter.get_stage_vals(), params).build()

def zkpFunc(dataset_query_dict: dict):
    params: dict = {
        "k": 19,
        "paramgen": False,
        "param": f"./proof/super_param.bin",
        "proofgen": False
    }
    for dataset in dataset_query_dict.keys():
        path = dataset_query_dict[dataset]["path"]
        graph: Graph = load_dataset(path)
        queries: list[str] = dataset_query_dict[dataset]["queries"]

        for query_str in queries:
            log_and_write(f"----- Experimenting {query_str} -----")
            query_name = os.path.basename(query_str).split('.')[0]
            query: str = load_query(query_str)
            params["proof"] = f"./proof/super_proof_{dataset}_{query_name}"
            with open(LOG_FILE, "a") as file:
                logtee = TeeLog(sys.stdout, file)
                with redirect_stdout(logtee):
                    performZKP(graph, query, params)

if __name__ == "__main__":
    dataset_query_dict = {
        "swdf": {
            "path": "./datasets/swdf/swdf.nt",
            "queries": [
                "./datasets/swdf/sparql_queries/q1.sparql",
                "./datasets/swdf/sparql_queries/q2.sparql",
                "./datasets/swdf/sparql_queries/q3.sparql",
                "./datasets/swdf/sparql_queries/q4.sparql",
                "./datasets/swdf/sparql_queries/q5.sparql",
            ]
        },
        "drugbank": {
            "path": "./datasets/drugbank/drugbank.nt",
            "queries": [
                "./datasets/drugbank/sparql_queries/q1.sparql",
                "./datasets/drugbank/sparql_queries/q2.sparql",
                "./datasets/drugbank/sparql_queries/q3.sparql",
                "./datasets/drugbank/sparql_queries/q4.sparql",
                "./datasets/drugbank/sparql_queries/q5.sparql",
            ]
        },
        "bsbm": {
            "path": "./datasets/bsbm/bsbm.nt",
            "queries": [
                "./datasets/bsbm/sparql_queries/q1.sparql",
                "./datasets/bsbm/sparql_queries/q2.sparql",
                "./datasets/bsbm/sparql_queries/q3.sparql",
                "./datasets/bsbm/sparql_queries/q4.sparql",
                "./datasets/bsbm/sparql_queries/q5.sparql",
            ]
        }
    }
    zkpFunc(dataset_query_dict)