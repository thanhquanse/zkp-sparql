import rdflib
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler

g = Graph()

data = """
@prefix ex: <http://example.org/> .
@prefix schema: <http://schema.org/> .

ex:review1 a ex:Review ;
    ex:product ex:productA ;
    ex:rating 4 .

ex:review2 a ex:Review ;
    ex:product ex:productA ;
    ex:rating 5 .

ex:review3 a ex:Review ;
    ex:product ex:productB ;
    ex:rating 2 .

ex:review4 a ex:Review ;
    ex:product ex:productB ;
    ex:rating 3 .

ex:review5 a ex:Review ;
    ex:product ex:productC ;
    ex:rating 5 .

ex:review6 a ex:Review ;
    ex:product ex:productC ;
    ex:rating 5 .
"""

query = """
PREFIX ex: <http://example.org/>

SELECT ?product (SUM(?rating) AS ?sumRating)
WHERE {
  ?review a ex:Review ;
          ex:product ?product ;
          ex:rating ?rating .
}
GROUP BY ?product
HAVING (SUM(?rating) >= 4)
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data=data, format="turtle")
results = g.query(query)
ZKPSingleHandler(stage_extracter.get_stage_vals()).build()