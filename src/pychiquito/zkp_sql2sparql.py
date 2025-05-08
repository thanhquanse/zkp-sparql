import rdflib
import time
import morph_kgc
from memory_profiler import profile
from functools import wraps
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.superhandler import ZKPSuperHandler

csv_dataset = './relationaldb/lineitem.tbl'
config_file = './relationaldb/config.ini'
sparql = """
PREFIX ex: <http://example.com/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?returnFlag ?lineStatus
    (SUM(?quantity) AS ?sum_qty)
    (SUM(?extendedPrice) AS ?sum_base_price)
    #(SUM(?extendedPrice * (1 - ?discount)) AS ?sum_disc_price)
    #(SUM(?extendedPrice * (1 - ?discount) * (1 + ?tax)) AS ?sum_charge)
    (SUM(?extendedPrice) AS ?sum_disc_price)
    (SUM(?extendedPrice) AS ?sum_charge)
    (AVG(?quantity) AS ?avg_qty)
    (AVG(?extendedPrice) AS ?avg_price)
    (AVG(?discount) AS ?avg_disc)
    (COUNT(?s) AS ?count_order)
WHERE {
  ?s a ex:LineItem ;
     ex:returnFlag ?returnFlag ;
     ex:lineStatus ?lineStatus ;
     ex:quantity ?quantity ;
     ex:extendedPrice ?extendedPrice ;
     ex:discount ?discount ;
     ex:tax ?tax ;
     ex:shipDate ?shipDate .
  FILTER (?shipDate <= "1998-08-03"^^xsd:date)
}
GROUP BY ?returnFlag ?lineStatus
ORDER BY ?returnFlag ?lineStatus
"""

def timeit(func):
  @wraps(func)
  def timeit_wrapper(*args, **kwargs):
      start_time = time.perf_counter()
      result = func(*args, **kwargs)
      end_time = time.perf_counter()
      total_time = end_time - start_time
      print(f'Function {func.__name__} took {total_time:.4f} seconds')
      return result
  return timeit_wrapper

@timeit
@profile
def performSPARL(graph: Graph, query: str):
    return graph.query(query)

@timeit
@profile
def func():
    params: dict = {
        "k": 17,
        "param": "./proof/super_params_sql2sparql_test.bin",
        "paramgen": True,
        "proof": "./proof/super_proof_sql2sparql_test.bin",
        "proofgen": True
    }
    graph: Graph = morph_kgc.materialize(config_file)
    stage_extracter = StageExtracter()
    rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval
    results = performSPARL(graph, sparql)
    ZKPSuperHandler(stage_extracter.get_stage_vals(), params).build()

if __name__ == '__main__':
    func()