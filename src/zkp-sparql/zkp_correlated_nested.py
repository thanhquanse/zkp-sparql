import os
import sys
import rdflib
from contextlib import redirect_stdout
from memory_profiler import profile
from rdflib import Graph, ConjunctiveGraph
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

def load_dataset(path: str, is_conjunctive=False) -> Graph:
    # Conjunctive graph
    if is_conjunctive:
        cg = ConjunctiveGraph()
        cg.parse(path, format="trig")
        print(f"Loaded conjunctive graph {path} with size: {len(cg)}")
        return cg
    
    # Normal graph
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

# @timeit
# @profile
def performSPARQL(graph: Graph, query: str):
    return graph.query(query)

# @timeit
# @profile
def performZKP(graph: Graph, query: str, params: dict):
    stage_extracter = StageExtracter()
    rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval
    results = performSPARQL(graph, query)
    
    for rs in results:
        print(rs)
        # print(f"{rs.product} - {rs.label}")
        # print(f"{rs.product} - {rs.label} - {rs.p1} - {rs.p3}")

    # return
    ZKPSuperHandler(stage_extracter.get_stage_vals(), params).build()

# @timeit
# @profile
def process_dataset_query(dataset_query_dict: dict):
    params: dict = {
        "k": 19,
        "paramgen": True,
        "param": f"./proof/super_param.bin",
        "proofgen": True,
        "step_num": 100000
    }
    for dataset in dataset_query_dict.keys():
        path = dataset_query_dict[dataset]["path"]
        graph: Graph = load_dataset(path, is_conjunctive=dataset_query_dict[dataset]["is_conjunctive"])
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
        "bsbm": {
            "path": "./datasets/bsbm/bsbm_light.nt",
            "queries": [
                "./datasets/bsbm/corr_sparql_queries/q1_corr_select.sparql", # OK
                "./datasets/bsbm/corr_sparql_queries/q2_corr_select.sparql", # OK
                "./datasets/bsbm/sparql_queries/q6_describe.sparql", # OK
                "./datasets/bsbm/sparql_queries/q7_construct.sparql", # OK
            ],
            "is_conjunctive": False
        },
        "drugbank": {
            "path": "./datasets/drugbank/drugbank_light.nt",
            "queries": [
                "./datasets/drugbank/corr_sparql_queries/q1_corr_select.sparql", # Killed
                "./datasets/drugbank/sparql_queries/q6_describe.sparql", # OK
                "./datasets/drugbank/sparql_queries/q7_construct.sparql" # OK
            ],
            "is_conjunctive": False
        },
        "swdf": {
            "path": "./datasets/swdf/swdf_light.nt",
            "queries": [
                "./datasets/swdf/sparql_queries/q6_describe.sparql", # OK
                "./datasets/swdf/sparql_queries/q7_construct.sparql", # OK
                "./datasets/swdf/corr_sparql_queries/q1_corr_select.sparql", # Killed
                "./datasets/swdf/corr_sparql_queries/q2_corr_select.sparql" # Killed
            ],
            "is_conjunctive": False
        },
        "bsbm_named_graph": {
            "path": "./datasets/bsbm/bsbm_named_graphs.trig",
            "queries": [
                "./datasets/bsbm/sparql_queries/q8_graph.sparql", # OK
                "./datasets/bsbm/sparql_queries/q9_graph.sparql" # OK
            ],
            "is_conjunctive": True
        }
    }
    process_dataset_query(dataset_query_dict)