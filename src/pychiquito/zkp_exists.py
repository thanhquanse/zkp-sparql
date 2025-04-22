import rdflib
from rdflib import Graph
from libs.stage_extracter import StageExtracter
from libs.zkp_handler import ZKPHandler

g = Graph()

data = """
@prefix ex: <http://example.org/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

ex:alice a foaf:Person ;
    foaf:name "Alice" .

ex:bob a foaf:Person ;
    foaf:name "Bob" ;
    ex:hasPublished ex:book1 .

ex:carol a foaf:Person ;
    foaf:name "Carol" ;
    ex:hasPublished ex:book2 .

ex:book1 a ex:Book ;
    ex:title "SPARQL for Beginners" .

ex:book2 a ex:Book ;
    ex:title "Advanced RDF Techniques" .
"""

query = """
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?person ?name
WHERE {
  ?person a foaf:Person ;
          foaf:name ?name .
  FILTER EXISTS {
    ?person ex:hasPublished ?book .
  }
}
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data=data, format="turtle")
results = g.query(query)
ZKPHandler(stage_extracter.get_stage_vals()).build()