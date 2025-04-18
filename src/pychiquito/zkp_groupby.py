import rdflib
from rdflib import Graph
from libs.stage_extracter import StageExtracter
from libs.zkp_handler import ZKPHandler

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

query = """
PREFIX ex: <http://example.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

# TODO: Functions in variables
SELECT ?category
       (COUNT(?book) AS ?count)
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

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["exampleEval"] = stage_extracter.customEval

g.parse(data=data, format="turtle")
results = g.query(query)
ZKPHandler(stage_extracter.get_stage_vals()).build()