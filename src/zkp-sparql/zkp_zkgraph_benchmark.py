import rdflib
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler

g = Graph()

query = """
PREFIX sn: <http://www.ldbc.eu/ldbc_socialnet/1.0/data/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX snvoc: <http://www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?knownFriend ?friendFirstName ?friendLastName ?creationDate
WHERE {
   {
      sn:pers933 snvoc:knows ?knownFriendNode .
      ?knownFriendNode snvoc:hasPerson ?knownFriend .
    } UNION {
      ?knownFriend snvoc:knows ?knownFriendNode .
      ?knownFriendNode snvoc:hasPerson sn:pers933 .
   }
    ?knownFriendNode snvoc:creationDate ?creationDate .
    ?knownFriend snvoc:firstName ?friendFirstName ;
                 snvoc:lastName ?friendLastName .
} ORDER BY DESC(?creationDate) ?knownFriend
"""

query_1 = """
PREFIX sn: <http://www.ldbc.eu/ldbc_socialnet/1.0/data/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX snvoc: <http://www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?knownFriend ?friendFirstName ?friendLastName ?creationDate
WHERE {
  {
    sn:pers933 snvoc:knows/snvoc:hasPerson ?knownFriend .
  } UNION {
    ?knownFriend snvoc:knows/snvoc:hasPerson sn:pers933 .
  }
  ?knownFriend snvoc:knowsCreationDate ?creationDate ;
               snvoc:firstName ?friendFirstName ;
               snvoc:lastName ?friendLastName .
}
ORDER BY DESC(?creationDate) ?knownFriend
"""

query_2 = """
PREFIX sn: <http://www.ldbc.eu/ldbc_socialnet/1.0/data/>
PREFIX snvoc: <http://www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/>

SELECT ?knownFriend ?friendFirstName ?friendLastName ?creationDate
WHERE {
  {
    sn:pers933 snvoc:knows/snvoc:hasPerson ?knownFriend .
    ?knownFriend snvoc:creationDate ?creationDate .
  } UNION {
    ?knownFriend snvoc:knows/snvoc:hasPerson sn:pers933 .
    ?knownFriend snvoc:creationDate ?creationDate .
  }
  ?knownFriend snvoc:firstName ?friendFirstName ;
               snvoc:lastName ?friendLastName .
}
ORDER BY DESC(?creationDate) ?knownFriend
"""

person_query_is1 = """
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

msg_query_is4 = """
PREFIX sn:     <http://www.ldbc.eu/ldbc_socialnet/1.0/data/>
PREFIX snvoc:  <http://www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/>
PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>

# PARAM: $messageId = 1009
SELECT 
  ?messageCreationDate
  ?messageContent
WHERE {
  sn:msg1009
    a snvoc:Message ;
    snvoc:creationDate ?messageCreationDate ;
    snvoc:content ?messageContent .
}
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse('./datasets/zkgraph/person_fact_sample.ttl', format="turtle")

print(f"Number of triples in graph: {len(g)}")
results = g.query(person_query_is1)

print(f"Number of results: {len(list(results))}")
# for r in results:
#     print(r)
ZKPSingleHandler(stage_extracter.get_stage_vals()).build()