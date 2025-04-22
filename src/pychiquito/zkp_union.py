import rdflib
from rdflib import Graph
from libs.stage_extracter import StageExtracter
from libs.zkp_handler import ZKPHandler

g = Graph()

data ="""
@prefix ex: <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:book1  ex:title "SPARQL Basics" ;          ex:author "Alice" ;     ex:year "2020"^^xsd:gYear .
ex:book2  ex:title "Advanced SPARQL" ;        ex:author "Bob" ;       ex:year "2021"^^xsd:gYear .
ex:book3  ex:title "RDF for Dummies" ;        ex:author "Alice" ;     ex:year "2022"^^xsd:gYear .
ex:book4  ex:title "Ontology Engineering" ;   ex:author "Carol" ;     ex:year "2023"^^xsd:gYear .
ex:book5  ex:title "Linked Data 101" ;        ex:author "David" ;     ex:year "2022"^^xsd:gYear .
ex:book6  ex:title "Graph DB Internals" ;     ex:author "Alice" ;     ex:year "2023"^^xsd:gYear .
ex:book7  ex:title "SPARQL Advanced Topics" ; ex:author "Eve" ;       ex:year "2020"^^xsd:gYear .
ex:book8  ex:title "Turtle Syntax Deep Dive" ; ex:author "Frank" ;    ex:year "2021"^^xsd:gYear .
ex:book9  ex:title "Semantic Web Essentials" ; ex:author "Grace" ;    ex:year "2022"^^xsd:gYear .
ex:book10 ex:title "Chaining Reasoners" ;     ex:author "Heidi" ;     ex:year "2023"^^xsd:gYear .
ex:book11 ex:title "Reasoning at Scale" ;     ex:author "Ivan" ;      ex:year "2020"^^xsd:gYear .
"""

query = """
PREFIX ex: <http://example.org/>

SELECT ?book ?title ?author ?year
WHERE {
  {
    ?book ex:title ?title ;
          ex:author "Alice" ;
          ex:author ?author ;
          ex:year ?year .
  }
  UNION
  {
    ?book ex:title ?title ;
          ex:author ?author ;
          ex:year "2023" ;
          ex:year ?year .
  }
}
ORDER BY ?year
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data=data, format="turtle")
results = g.query(query)
ZKPHandler(stage_extracter.get_stage_vals()).build()