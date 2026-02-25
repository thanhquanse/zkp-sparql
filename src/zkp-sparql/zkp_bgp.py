import rdflib
from rdflib import Graph
from rdflib.plugins.sparql.parser import parseQuery
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler
from memory_profiler import profile
from utils.measure import timeit

g = Graph()

swdf_data_path = "./datasets/swdf/swdf_50_pct.nt"
drugbank_data_path = "./datasets/drugbank/drugbank_100_pct.nt"
bsbm_data_path = "./datasets/bsbm/bsbm_50_pct.nt"

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
ex:book12 ex:name "SPARQL Performance Tips" ; ex:price "22"^^xsd:decimal .
"""

query = """
prefix ex: <http://example.org/>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT *
WHERE {
    ?s1 ex:title ?o1 .
    ?s2 ex:price ?o2 .
}
"""

swdf_query = """
  PREFIX  owl:  <http://www.w3.org/2002/07/owl#>
  PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
  PREFIX  foaf: <http://xmlns.com/foaf/0.1/>

  SELECT ?resource_uri
  WHERE {
      ?resource_uri <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?concept .
  }
"""

drugbank_query = """
  SELECT ?s ?o WHERE {  
    ?s <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugbank/generalReference> ?o.
  }
"""

bsbm_query = """
  PREFIX bsbm-inst: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/instances/>
  PREFIX bsbm: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/vocabulary/>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
  PREFIX dc: <http://purl.org/dc/elements/1.1/>

  SELECT ?product ?productFeature
  WHERE {
    ?product bsbm:productFeature ?productFeature .
  }
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data=data, format="turtle")
# g.parse(".//rdf2rdb/datasets/BSBM.ttl")
print(f"Graph size: {len(g)}")
results = g.query(query)
# for row in results:
#     print(row)

@timeit
@profile
def func():
  ZKPSingleHandler(stage_extracter.get_stage_vals()).build()

if __name__ == "__main__":
  func()