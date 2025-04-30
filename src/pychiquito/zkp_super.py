import rdflib
from memory_profiler import profile
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler
from libs.superhandler import ZKPSuperHandler

data = """
@prefix ex: <http://example.org/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

# Authors
ex:alice a foaf:Person ; foaf:name "Alice" .
ex:bob a foaf:Person ; foaf:name "Bob" .
ex:carol a foaf:Person ; foaf:name "Carol" .

# Books
ex:book1 a ex:Book ; ex:title "SPARQL Basics" ; ex:author ex:alice ; ex:price 25 ; ex:category "Programming" .
ex:book2 a ex:Book ; ex:title "Advanced SPARQL" ; ex:author ex:bob ; ex:price 35 ; ex:category "Programming" .
ex:book3 a ex:Book ; ex:title "Semantic Web" ; ex:author ex:carol ; ex:price 45 ; ex:category "Semantics" .
ex:book4 a ex:Book ; ex:title "Data Modeling" ; ex:author ex:carol ; ex:price 40 ; ex:category "Data" .
ex:book5 a ex:Book ; ex:title "SPARQL for Pros" ; ex:price 30 ; ex:category "Programming" . # No author

# Out-of-scope books (for MINUS)
ex:bookX a ex:Book ; ex:title "Excluded Book" ; ex:author ex:bob ; ex:price 50 ; ex:category "Other" .
"""

query = """
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT DISTINCT ?authorName (COUNT(?book) AS ?numBooks) (AVG(?price) AS ?avgPrice)
WHERE {
  {
    # UNION to allow both authored and unauthored books
    {
      ?book a ex:Book ;
            ex:author ?author ;
            ex:price ?price ;
            ex:category ?category .
      ?author foaf:name ?authorName .
    }
    UNION
    {
      ?book a ex:Book ;
            ex:price ?price ;
            ex:category ?category .
      OPTIONAL { ?book ex:author ?author . ?author foaf:name ?authorName . }
    }
  }

  # FILTER: only programming books
  FILTER(?category = "Programming")
#   FILTER EXISTS {
#     ?author foaf:name ?authorName .
#   }

  # MINUS: exclude certain books explicitly
  MINUS {
    ?book ex:title "Excluded Book" .
  }
}
GROUP BY ?authorName
HAVING(AVG(?price) > 1)
ORDER BY DESC(?avgPrice)
LIMIT 2
OFFSET 1
"""

g = Graph()
g.parse(data=data, format="turtle")
print(f"Loaded graph: {len(g)}")

@profile
def func():
  stage_extracter = StageExtracter()
  rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval
  results = g.query(query)
  ZKPSuperHandler(stage_extracter.get_stage_vals()).build()

if __name__ == '__main__':
    func()