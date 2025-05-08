import rdflib
import time
from memory_profiler import profile
from functools import wraps
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler
from libs.superhandler import ZKPSuperHandler

g = Graph()

data = "./datasets/swdf/swdf_light.nt"

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

query_ask = """
PREFIX  owl:  <http://www.w3.org/2002/07/owl#>
PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  foaf: <http://xmlns.com/foaf/0.1/>

ASK {
    ?resource_uri <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?concept .
    ?resource_uri ?property ?value .
    FILTER(?value = "a")
}
"""

query_complex = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX swrc: <http://swrc.ontoware.org/ontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?author
       (COUNT(DISTINCT ?paper) AS ?numPapers)
       (AVG(?titleLength) AS ?avgTitleLength)
       (SUM(?titleLength) AS ?totalTitleLength)
       (MIN(?titleLength) AS ?minTitleLength)
       (MAX(?titleLength) AS ?maxTitleLength)
WHERE {
  {
    # Case 1: Paper directly linked via foaf:made
    ?author a foaf:Person ;
            foaf:name ?authorName ;
            foaf:made ?paper .
  }
  UNION
  {
    # Case 2: Paper authorship via rdf:_n list
    ?author a foaf:Person ;
            foaf:name ?authorName .
    ?authList ?pos ?author .
    ?authList ^<http://data.semanticweb.org/ns/swc/ontology#hasRelatedDocument> ?paper .
  }

  ?paper rdfs:label ?title .
  OPTIONAL { ?paper swrc:year ?year . }

  # Convert title to string length
  BIND(STRLEN(STR(?title)) AS ?titleLength)

  # FILTER: only papers from year 2006 or later
  FILTER(xsd:integer(?year) >= 2006)

  # MINUS: exclude papers by exact title
  MINUS {
    ?paper rdfs:label "OPTIMA:  A System for Semi Automatic and Large Scale Ontology Population" .
  }
}
GROUP BY ?author
HAVING(SUM(?titleLength) > 10)
ORDER BY DESC(?avgTitleLength)
LIMIT 5
OFFSET 3
"""

def timeit(func):
  @wraps(func)
  def timeit_wrapper(*args, **kwargs):
      start_time = time.perf_counter()
      result = func(*args, **kwargs)
      end_time = time.perf_counter()
      total_time = end_time - start_time
      print(f'Function {func.__name__} took {total_time:.4f} seconds')
      return result
  return timeit_wrapper

g.parse(data)
print(f"Loaded graph: {len(g)}")

@timeit
def execute_query():
  results = g.query(query_complex)
  for row in results:
    print(f"Author name: {row.author}, {row.numPapers}, {row.avgTitleLength}")
  # print("ASK result:", results.askAnswer)

@profile
@timeit
def func():
  params: dict = {
    "k": 17,
    "param": "./proof/super_params_test.bin",
    "paramgen": True,
    "proof": "./proof/super_proof_test.bin",
    "proofgen": True
  }
  stage_extracter = StageExtracter()
  rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval
  results = g.query(query_complex)
  ZKPSuperHandler(stage_extracter.get_stage_vals(), params).build()

if __name__ == '__main__':
    func()