import rdflib
from rdflib import Graph
from libs.stage_extracter import StageExtracter
from libs.zkp_handler import ZKPHandler

g = Graph()

data = """
@prefix ex: <http://example.org/> .

ex:book1  ex:title "SPARQL Basics" ;          ex:author "Alice" .
ex:book2  ex:title "Advanced SPARQL" ;        ex:author "Bob" .
ex:book3  ex:title "SPARQL Basics" ;          ex:author "Alice" .
ex:book4  ex:title "RDF Primer" ;             ex:author "Carol" .
ex:book5  ex:title "SPARQL Optimization" ;    ex:author "Bob" .
ex:book6  ex:title "Linked Data" ;            ex:author "Dave" .
ex:book7  ex:title "RDF Primer" ;             ex:author "Carol" .
ex:book8  ex:title "SPARQL Federation" ;      ex:author "Alice" .
ex:book9  ex:title "SPARQL Update" ;          ex:author "Eve" .
ex:book10 ex:title "Graph Databases" ;        ex:author "Frank" .
ex:book11 ex:title "SPARQL Basics" ;          ex:author "Grace" .
ex:book12 ex:title "Semantic Search" ;        ex:author "Grace" .
"""

query = """
PREFIX ex: <http://example.org/>

SELECT DISTINCT ?author
WHERE {
  ?book ex:author ?author .
  FILTER(?author != "Bob")
}
ORDER BY DESC(?author)
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data=data, format="turtle")
results = g.query(query)
ZKPHandler(stage_extracter.get_stage_vals()).build()