import rdflib
from rdflib import Graph
from libs.stage_extracter import StageExtracter
from libs.zkp_handler import ZKPHandler

g = Graph()

data = """
@prefix ex: <http://example.org/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

ex:book1  ex:title "SPARQL Basics" ; ex:author ex:alice .
ex:book2  ex:title "Advanced SPARQL" ; ex:author ex:bob .
ex:book3  ex:title "SPARQL for Dummies" .
ex:book4  ex:title "SPARQL with RDF" ; ex:author ex:carol .
ex:book5  ex:title "Querying the Web" .
ex:book6  ex:title "Linked Data 101" ; ex:author ex:alice .
ex:book7  ex:title "RDF Deep Dive" ; ex:author ex:dave .
ex:book8  ex:title "Semantic Web in Practice" .
ex:book9  ex:title "Ontology Design" ; ex:author ex:carol .
ex:book10 ex:title "Data Integration with SPARQL" ; ex:author ex:bob .
ex:book11 ex:title "RDF Graphs" .

ex:alice foaf:name "Alice" .
ex:bob foaf:name "Bob" .
ex:carol foaf:name "Carol" .
ex:dave foaf:name "Dave" .
"""

query = """
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?book ?title
WHERE {
  ?book ex:title ?title .
  OPTIONAL { ?book ex:author ?author . }
  MINUS {
    ?book ex:author ex:bob .
  }
}
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data=data, format="turtle")
results = g.query(query)
ZKPHandler(stage_extracter.get_stage_vals()).build()