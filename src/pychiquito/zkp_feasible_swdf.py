import rdflib
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler

g = Graph()

data = "./datasets/feasible_swdf.nt"

query_1 = """
PREFIX  owl:  <http://www.w3.org/2002/07/owl#>
PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?a ?v0
WHERE
  { ?a rdf:type foaf:Person .
    ?a foaf:name ?v0
  }
GROUP BY ?a
OFFSET  10000
LIMIT   1000
"""

query_2 = """
PREFIX  owl:  <http://www.w3.org/2002/07/owl#>
PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  foaf: <http://xmlns.com/foaf/0.1/>

SELECT DISTINCT  ?instance ?p ?o
WHERE
  { ?instance <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://xmlns.com/foaf/0.1/Person> .
    ?instance ?p ?o
  }
GROUP BY ?instance
ORDER BY ?instance ?p ?o
OFFSET  1000
LIMIT   1000
"""

query_3 = """
PREFIX  owl:  <http://www.w3.org/2002/07/owl#>
PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  foaf: <http://xmlns.com/foaf/0.1/>

SELECT  ?resource_uri (count(?property) AS ?datatype_properties)
WHERE
  { ?resource_uri <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?concept .
    ?resource_uri ?property ?value
  }
GROUP BY ?resource_uri
OFFSET  8000
LIMIT   1000
"""

query_4 = """
PREFIX  skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX  foaf: <http://xmlns.com/foaf/0.1/>

SELECT DISTINCT  ?person_uri ?person_name
WHERE
  { ?person_uri <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> foaf:Person
      { ?person_uri skos:prefLabel ?person_name }
    UNION
      { ?person_uri foaf:name ?person_name
        OPTIONAL
          { ?person_uri skos:prefLabel ?prefLabel }
        FILTER regex(str(?person_name), "a", "i")
      }
    FILTER regex(str(?person_uri), "^http://data.semanticweb.org", "i")
  }
ORDER BY ?person_uri
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data)
print(f"Loaded graph: {len(g)}")
results = g.query(query_4)
ZKPSingleHandler(stage_extracter.get_stage_vals()).build()