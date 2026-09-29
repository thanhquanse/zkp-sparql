import rdflib
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler

g = Graph()

is5 = """
PREFIX sn:     <http://www.ldbc.eu/ldbc_socialnet/1.0/data/>
PREFIX snvoc:  <http://www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/>
PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>

SELECT 
  ?firstName
  ?lastName
  ?birthday
  ?browserUsed
  ?gender
  ?creationDate
WHERE {
  sn:pers10008
    snvoc:firstName ?firstName ;
    snvoc:lastName ?lastName ;
    snvoc:birthday ?birthday ;
    snvoc:locationIP ?locationIP ;
    snvoc:browserUsed ?browserUsed ;
    snvoc:gender ?gender ;
    snvoc:creationDate ?creationDate .
}
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse('./datasets/zkgraph/person_fact_sample.ttl', format="turtle")

print(f"Number of triples in graph: {len(g)}")
results = g.query(is5)

print(f"Number of results: {len(list(results))}")
# for r in results:
#     print(r)
ZKPSingleHandler(stage_extracter.get_stage_vals()).build()