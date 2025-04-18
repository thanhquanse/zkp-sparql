import rdflib
from rdflib import Graph
from libs.stage_extracter import StageExtracter
from libs.zkp_handler import ZKPHandler

g = Graph()

data = """
@prefix ex: <http://example.org/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

ex:book1 a ex:Book ; ex:title "SPARQL Basics" ; ex:author ex:alice .
ex:book2 a ex:Book ; ex:title "Advanced SPARQL" ; ex:author ex:bob .
ex:book3 a ex:Book ; ex:title "SPARQL for Dummies" .
ex:book4 a ex:Book ; ex:title "SPARQL with RDF" ; ex:author ex:carol .
ex:book5 a ex:Book ; ex:title "Querying the Web" .
ex:book6 a ex:Book ; ex:title "Linked Data 101" ; ex:author ex:alice .
ex:book7 a ex:Book ; ex:title "RDF Deep Dive" ; ex:author ex:dave .
ex:book8 a ex:Book ; ex:title "Semantic Web in Practice" .
ex:book9 a ex:Book ; ex:title "Ontology Design" ; ex:author ex:carol .
ex:book10 a ex:Book ; ex:title "Data Integration with SPARQL" ; ex:author ex:bob .
ex:book11 a ex:Book ; ex:title "RDF Graphs" .

ex:alice foaf:name "Alice" .
ex:bob foaf:name "Bob" .
ex:carol foaf:name "Carol" .
ex:dave foaf:name "Dave" .
"""

query = """
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?book ?title ?authorName
WHERE {
  ?book a ex:Book ;
        ex:title ?title .
  OPTIONAL {
    ?book ex:author ?author .
    ?author foaf:name ?authorName .
  }
}
ORDER BY ?book
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["exampleEval"] = stage_extracter.customEval

g.parse(data=data, format="turtle")
results = g.query(query)
ZKPHandler(stage_extracter.get_stage_vals()).build()