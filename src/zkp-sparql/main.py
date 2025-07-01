import os
import json
import rdflib
import datetime
import time
from pathlib import Path
from memory_profiler import memory_usage, profile
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.superhandler import ZKPSuperHandler
from libs.singlehandler import ZKPSingleHandler

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = f"./logs/experiment_{timestamp}.log"
# MEM_LOG_FILE = f"./logs/profile_experiment_{timestamp}.log"
# logging.basicConfig(filename=MEM_LOG_FILE, level=logging.INFO)

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

def print_and_write(message: str, logfile: str = LOG_FILE):
    print(f"{message}\n")
    with open(logfile, "a") as file:
        file.write(f"{message}\n")

def load_dataset(path: str) -> Graph:
    g = Graph()
    if Path(path).suffix == '.ttl':
        g.parse(path, format="turtle")
    else:
        g.parse(path)
    print_and_write(f"INFO: Loaded graph {path} with size: {len(g)}")

    return g

def load_query(path: str) -> str:
    if not os.path.exists(path):
        print_and_write(f"Error: File {path} not found")
        exit(1)

    try:
        with open(path, "r") as file:
            sparql_query = file.read()
    except IOError as e:
        print_and_write(f"Error: reading file {path}: {e}")
        exit(1)
    
    return sparql_query

def select_k(ds_size: int) -> int:
    if ds_size < 65536:
        return 16, 65000
    elif ds_size < 130000:
        return 17, 100000
    elif ds_size < 260000:
        return 18, 150000
    elif ds_size < 520000:
        return 19, 250000
    elif ds_size < 1048576:
        return 20, 500000 
    else:
        return 22, 1000000

def process_query(graph: Graph, query: str):
    return graph.query(query)

@profile
def perform_zkp_circuit(graph: Graph, query: str, params: dict, is_single=False):
    stage_extracter = StageExtracter()
    rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval
    print_and_write(f"INFO: Param proof {params['proof']}...")

    start = time.time()
    results = process_query(graph, query)
    print_and_write(f"INFO: Number of query results: {len(list(results))}")
    end = time.time()
    print_and_write(f"INFO: Query execution time: {end - start}\n")
    
    start = time.time()
    if is_single:
        zkp_exe_results = ZKPSingleHandler(stage_extracter.get_stage_vals()).build()
    else:
        zkp_exe_results = ZKPSuperHandler(stage_extracter.get_stage_vals(), params).build(log_path=LOG_FILE)
    end = time.time()
    print_and_write(f"INFO: perform_zkp execution time: {end - start}\n")
    
    return zkp_exe_results

def process_dataset_query(dataset_query_dict: dict, is_single=False):
    for dataset in dataset_query_dict.keys():
        path = dataset_query_dict[dataset]["path"]
        graph: Graph = load_dataset(path)
        queries: list[str] = dataset_query_dict[dataset]["queries"]
        Path(f"./proof/{dataset}").mkdir(parents=True, exist_ok=True)

        k, step_num = select_k(len(graph))
        param_file_path = f"./proof/param_{str(k)}.bin"

        for query_str in queries:
            print_and_write(f"--------------- Experimenting: {dataset} - {query_str} ---------------")

            query_name = os.path.basename(query_str).split('.')[0]
            query: str = load_query(query_str)
            params: dict = {
                "k": k,
                "step_num": step_num,
                "param": param_file_path,
                "paramgen": (not os.path.exists(param_file_path)),
                "proofgen": True,
                "proof": f"./proof/{dataset}/{'single' if is_single else 'super'}_proof_{query_name}"
            }

            print_and_write(f"INFO: Params: {json.dumps(params)}")
            
            # exe_results = perform_zkp_circuit(graph, query, params, is_single)

            mem_usage, exe_results = memory_usage((perform_zkp_circuit, (graph, query, params, is_single)), retval=True, interval=0.1, max_usage=True)
            # logging.info(f"Params: query={query_str}, Peak memory: {mem_usage:.2f} MB")

            print_and_write(f"INFO: Mem usage: {mem_usage:.2f} MB")
            print_and_write(f"INFO: Proving time: {exe_results['proving']}")
            print_and_write(f"INFO: Param gen time: {exe_results['param_gen']}")
            print_and_write(f"INFO: Proof gen time: {exe_results['proof_gen']}")

            print_and_write("-----------------------------------------------------Done-----------------------------------------------------\n")

def eval_super_gate():
    percentages = ["25", "50", "100"]

    for pct in percentages:
        dataset_query_dict = {
            "swdf": {
                "path": f"./datasets/swdf/swdf_{pct}_pct.nt",
                "queries": [
                    "./datasets/swdf/benchmark_queries/q1_select.sparql",
                    "./datasets/swdf/benchmark_queries/q2_select.sparql",
                    "./datasets/swdf/benchmark_queries/q3_select.sparql",
                    "./datasets/swdf/benchmark_queries/q4_ask.sparql",
                    "./datasets/swdf/benchmark_queries/q5_select.sparql",
                ]
            },
            "drugbank": {
                "path": f"./datasets/drugbank/drugbank_{pct}_pct.nt",
                "queries": [
                    "./datasets/drugbank/benchmark_queries/q1_select.sparql",
                    "./datasets/drugbank/benchmark_queries/q2_select.sparql",
                    "./datasets/drugbank/benchmark_queries/q3_select.sparql",
                    "./datasets/drugbank/benchmark_queries/q4_ask.sparql",
                    "./datasets/drugbank/benchmark_queries/q5_select.sparql",
                ]
            },
            "bsbm": {
                "path": f"./datasets/bsbm/bsbm_{pct}_pct.nt",
                "queries": [
                    "./datasets/bsbm/benchmark_queries/q1_select.sparql",
                    "./datasets/bsbm/benchmark_queries/q2_select.sparql",
                    "./datasets/bsbm/benchmark_queries/q3_select.sparql",
                    "./datasets/bsbm/benchmark_queries/q4_ask.sparql",
                    "./datasets/bsbm/benchmark_queries/q5_select.sparql",
                ]
            }
        }
        process_dataset_query(dataset_query_dict)

def eval_bsbm_converted():
    dataset_query_dict = {
        "bsbm_converted": {
            "path": "./rdf2rdb/datasets/BSBM.ttl",
            "queries": [
                "./rdf2rdb/sparql_queries/q1_select.sparql",
                "./rdf2rdb/sparql_queries/q3_select.sparql",
                "./rdf2rdb/sparql_queries/q4_select.sparql"
            ]
        }
    }
    process_dataset_query(dataset_query_dict)

def eval_single_gate():
    dataset_query_dict = {
        "swdf": {
            "path": "./datasets/swdf/swdf_100_pct.nt",
            "queries": [
                "./datasets/swdf/single_gate_benchmark_queries/q1_filter.sparql",
                "./datasets/swdf/single_gate_benchmark_queries/q2_group_order_by.sparql",
                "./datasets/swdf/single_gate_benchmark_queries/q3_aggregate.sparql",
                "./datasets/swdf/single_gate_benchmark_queries/q4_all.sparql"
            ]
        }
    }
    process_dataset_query(dataset_query_dict, is_single=True)

if __name__ == "__main__":
    eval_super_gate()
    eval_bsbm_converted()
    eval_single_gate()