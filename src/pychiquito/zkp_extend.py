import rdflib
from rdflib import Graph
from libs.stage_extracter import StageExtracter
from libs.zkp_handler import ZKPHandler

g = Graph()

data = """
@prefix ex: <http://example.org/> .

ex:book1 ex:title "SPARQL Basics" ;
         ex:price 30 .

ex:book2 ex:title "Advanced SPARQL" ;
         ex:price 25 .

ex:book3 ex:title "SPARQL for Dummies" ;
         ex:price 40 .
"""

query = """
SELECT ?book ?discountedPrice
WHERE {
  ?book ex:price ?price .
  BIND(?price / 0.9 AS ?discountedPrice)
}
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data=data, format="turtle")
results = g.query(query)
ZKPHandler(stage_extracter.get_stage_vals()).build()