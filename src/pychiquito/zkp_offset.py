import rdflib
from rdflib import Graph
from libs.stage_extracter import StageExtracter
from libs.zkp_handler import ZKPHandler

g = Graph()

data = """
@prefix ex: <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:book1  ex:title "SPARQL Basics" ;          ex:price "10"^^xsd:decimal .
ex:book2  ex:title "Advanced SPARQL" ;        ex:price "25"^^xsd:decimal .
ex:book3  ex:title "RDF for Dummies" ;        ex:price "15"^^xsd:decimal .
ex:book4  ex:title "Ontology Engineering" ;   ex:price "30"^^xsd:decimal .
ex:book5  ex:title "Linked Data 101" ;        ex:price "20"^^xsd:decimal .
ex:book6  ex:title "Graph DB Internals" ;     ex:price "40"^^xsd:decimal .
ex:book7  ex:title "SPARQL Advanced Topics" ; ex:price "35"^^xsd:decimal .
ex:book8  ex:title "Turtle Syntax Deep Dive" ; ex:price "18"^^xsd:decimal .
ex:book9  ex:title "Semantic Web Essentials" ; ex:price "12"^^xsd:decimal .
ex:book10 ex:title "Chaining Reasoners" ;     ex:price "50"^^xsd:decimal .
ex:book11 ex:title "Reasoning at Scale" ;     ex:price "45"^^xsd:decimal .
ex:book12 ex:title "SPARQL Performance Tips" ; ex:price "22"^^xsd:decimal .
"""

query = """
PREFIX ex: <http://example.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?book ?title ?price
WHERE {
  ?book ex:title ?title ;
        ex:price ?price .
  # FILTER(xsd:decimal(?price) > 20)
  FILTER(?price > 20)
}
ORDER BY ?price
OFFSET 2
LIMIT 5
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["exampleEval"] = stage_extracter.customEval

g.parse(data=data, format="turtle")
results = g.query(query)
ZKPHandler(stage_extracter.get_stage_vals()).build()