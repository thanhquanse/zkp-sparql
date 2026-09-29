import rdflib
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler
from memory_profiler import profile
from utils.measure import timeit

g = Graph()

data = """
@prefix ex: <http://example.org/> .

ex:book1 ex:author ex:alice .
ex:book2 ex:author ex:bob .
ex:book3 ex:author ex:alice .
ex:book4 ex:author ex:carol .

ex:alice ex:name "Alice" .
ex:bob ex:name "Bob" .
ex:carol ex:name "Carol" .
"""

data_path = "./datasets/swdf/swdf_light_60000.nt"

query = """
SELECT ?author ?authorName
WHERE {
  ?book ex:author ?author .
  ?author ex:name ?authorName .
}
GROUP BY ?author ?authorName
"""

query_str = """
PREFIX  owl:  <http://www.w3.org/2002/07/owl#>
PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  foaf: <http://xmlns.com/foaf/0.1/>

SELECT DISTINCT  ?instance ?p ?o
WHERE
  { ?instance <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://xmlns.com/foaf/0.1/Person> .
    ?instance ?p ?o
  }
GROUP BY ?instance
ORDER BY ?instance ?p ?o
OFFSET  10
LIMIT   1000
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data=data, format="turtle")
# g.parse(data_path)
results = g.query(query)

@timeit
@profile
def func():
  ZKPSingleHandler(stage_extracter.get_stage_vals()).build()

if __name__ == "__main__":
  func()