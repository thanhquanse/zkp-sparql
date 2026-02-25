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

ex:book1 ex:title "SPARQL Basics" ;
         ex:price "30"^^xsd:integer ;
         ex:category "Programming" .

ex:book2 ex:title "Learning RDF" ;
         ex:price "25"^^xsd:integer ;
         ex:category "Programming" .

ex:book3 ex:title "Advanced OWL" ;
         ex:price "40"^^xsd:integer ;
         ex:category "Semantics" .

ex:book4 ex:title "Linked Data 101" ;
         ex:price "20"^^xsd:integer ;
         ex:category "Data" .

ex:book5 ex:title "SPARQL Cookbook" ;
         ex:price "35"^^xsd:integer ;
         ex:category "Programming" .

ex:book6 ex:title "RDF Schema Guide" ;
         ex:price "28"^^xsd:integer ;
         ex:category "Semantics" .

ex:book7 ex:title "Data Integration" ;
         ex:price "22"^^xsd:integer ;
         ex:category "Data" .

ex:book8 ex:title "Reasoning with OWL" ;
         ex:price "45"^^xsd:integer ;
         ex:category "Semantics" .

ex:book9 ex:title "SPARQL Performance Tips" ;
         ex:price "32"^^xsd:integer ;
         ex:category "Programming" .

ex:book10 ex:title "Understanding URIs" ;
         ex:price "18"^^xsd:integer ;
         ex:category "Data" .

ex:book11 ex:title "Linked Data for Dummies" ;
         ex:price "26"^^xsd:integer ;
         ex:category "Data" .
"""

data_path = "./datasets/swdf/swdf_light_60000.nt"

query = """
PREFIX ex: <http://example.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

# TODO: Functions in variables
SELECT ?category
       (COUNT(?book) AS ?count)
    #    (SUM(xsd:integer(?price)) AS ?total_price)
    #    (AVG(xsd:integer(?price)) AS ?avg_price)
    #    (MAX(xsd:integer(?price)) AS ?max_price)
    #    (MIN(xsd:integer(?price)) AS ?min_price)
       (SUM(?price) AS ?total_price)
       (AVG(?price) AS ?avg_price)
       (MAX(?price) AS ?max_price)
       (MIN(?price) AS ?min_price)
WHERE {
  ?book ex:price ?price ;
        ex:category ?category .
}
GROUP BY ?category
ORDER BY ?category
"""

query_str = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX swrc: <http://swrc.ontoware.org/ontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?author
       (COUNT(DISTINCT ?paper) AS ?numPapers)
       (AVG(?titleLength) AS ?avgTitleLength)
       (SUM(?titleLength) AS ?totalTitleLength)
       (MIN(?titleLength) AS ?minTitleLength)
       (MAX(?titleLength) AS ?maxTitleLength)
WHERE {
  {
    # Case 1: Paper directly linked via foaf:made
    ?author a foaf:Person ;
            foaf:name ?authorName ;
            foaf:made ?paper .
  }

  ?paper rdfs:label ?title .

  # Convert title to string length
  BIND(STRLEN(STR(?title)) AS ?titleLength)
}
GROUP BY ?author
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