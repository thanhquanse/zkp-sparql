import rdflib
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler

g = Graph()

data = """
@prefix ex: <http://example.org/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

ex:book1 a ex:Book ;
    foaf:title "SPARQL Basics" ;
    ex:author ex:alice ;
    ex:price 30 ;
    ex:category "Programming" .

ex:book2 a ex:Book ;
    foaf:title "Advanced SPARQL" ;
    ex:author ex:bob ;
    ex:price 25 ;
    ex:category "Programming" .

ex:alice a foaf:Person ;
    foaf:name "Alice" .

ex:bob a foaf:Person ;
    foaf:name "Bob" .
"""

query = """
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

ASK {
  ?book a ex:Book ;
        ex:author ?author ;
        ex:price ?price ;
        ex:category ?category .

  ?author foaf:name "Alice" .

  FILTER(?price > 25)
}
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data=data, format="turtle")
results = g.query(query)
print("ASK result:", results.askAnswer)
ZKPSingleHandler(stage_extracter.get_stage_vals()).build()