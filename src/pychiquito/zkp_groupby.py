import rdflib
from rdflib import Graph
from libs.stage_extracter import StageExtracter
from libs.zkp_handler import ZKPHandler

g = Graph()

data = """
@prefix ex: <http://example.org/> .

ex:book1 ex:author ex:alice .
ex:book2 ex:author ex:bob .
ex:book3 ex:author ex:alice .
ex:book4 ex:author ex:carol .

ex:alice ex:name "Alice" .
ex:bob ex:name "Bob" .
ex:carol ex:name "Carol" .
"""

query = """
SELECT ?author ?authorName
WHERE {
  ?book ex:author ?author .
  ?author ex:name ?authorName .
}
GROUP BY ?author ?authorName
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data=data, format="turtle")
results = g.query(query)
ZKPHandler(stage_extracter.get_stage_vals()).build()