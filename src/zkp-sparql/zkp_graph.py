import rdflib
from rdflib import Graph, ConjunctiveGraph, URIRef
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler

g = Graph()

data = """
@prefix ex: <http://example.org/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

ex:alice a foaf:Person ;
        foaf:name "Alice" .

# Named graph: <http://example.org/graph1>
GRAPH <http://example.org/graph1> {
    ex:alice foaf:knows ex:bob .
    ex:bob a foaf:Person ;
           foaf:name "Bob" .
}

# Named graph: <http://example.org/graph2>
GRAPH <http://example.org/graph2> {
    ex:alice foaf:knows ex:charlie .
    ex:charlie a foaf:Person ;
               foaf:name "Charlie" .
}
"""

query = """
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?g ?person ?known ?name
WHERE {
    GRAPH ?g {
        ?person foaf:knows ?known .
        ?known foaf:name ?name .
    }
}
"""

filter = """
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?p ?name
WHERE {
  GRAPH ?g {
    ?p foaf:name ?name .
    FILTER(STRSTARTS(?name, "C"))   # name begins with C
  }
}
"""

optional = """
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?p ?name ?age
WHERE {
  GRAPH ?g {
    ?p foaf:name ?name .
    OPTIONAL { ?p ex:age ?age }
  }
}
"""

cg = ConjunctiveGraph()
cg.parse("./datasets/conjunctive-graph/test-dataset.trig", format="trig")

print("Named graphs found:")
for g in cg.contexts():
    print(" -", g.identifier)

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval
cg.query(filter)
ZKPSingleHandler(stage_extracter.get_stage_vals()).build()

for row in cg.query(optional):
    print(row)