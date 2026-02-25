import rdflib
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler
from memory_profiler import profile
from utils.measure import timeit

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

# TODO: Function in filter
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
"""

data_path = "./datasets/swdf/swdf_light_60000.nt"
query_str = """
PREFIX  owl:  <http://www.w3.org/2002/07/owl#>
PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?resource_uri
WHERE {
    ?resource_uri <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?concept .
    ?resource_uri ?property ?value .
    FILTER(REGEX(?value, "Nathalie Friburger", "i"))
}
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

# g.parse(data=data, format="turtle")
g.parse(data_path)
results = g.query(query_str)

@timeit
@profile
def func():
  ZKPSingleHandler(stage_extracter.get_stage_vals()).build()

if __name__ == "__main__":
  func()