import rdflib
import morph_kgc
from memory_profiler import profile
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.superhandler import ZKPSuperHandler
from utils.measure import timeit

csv_dataset = './relationaldb/lineitem_light.tbl'
config_file = './relationaldb/config.ini'
sparql = """
PREFIX ex: <http://zkpsparql.engine.com/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?returnFlag ?lineStatus
    (SUM(?quantity) AS ?sum_qty)
    (SUM(?extendedPrice) AS ?sum_base_price)
    (SUM(?extendedPrice * (1 - ?discount) * (1 + ?tax)) AS ?sum_charge)
    (SUM(?extendedPrice * (1 - ?discount)) AS ?sum_disc_price)
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
  FILTER (?shipDate <= "1998-09-01"^^xsd:date)
}
GROUP BY ?returnFlag ?lineStatus
ORDER BY ?returnFlag ?lineStatus
"""

@timeit
@profile
def performSPARQL(graph: Graph, query: str):
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
    results = performSPARQL(graph, sparql)
    ZKPSuperHandler(stage_extracter.get_stage_vals(), params).build()

if __name__ == '__main__':
    func()