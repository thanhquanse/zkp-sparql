import rdflib
from rdflib import Graph
from libs.stage_extracter import StageExtracter
from libs.zkp_handler import ZKPHandler

g = Graph()
g.parse(data="""
@prefix ex: <http://example.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:book1 rdf:type ex:Book ;
         rdfs:label "Learning Python" ;
         ex:pubYear "2015"^^xsd:integer ;
         ex:sales "5000"^^xsd:integer ;
         ex:author ex:author1 ;
         ex:category "Programming" .

ex:book2 rdf:type ex:Book ;
         rdfs:label "Python Crash Course" ;
         ex:pubYear "2015"^^xsd:integer ;
         ex:sales "8000"^^xsd:integer ;
         ex:author ex:author2 ;
         ex:category "Programming" .

ex:book3 rdf:type ex:Book ;
         rdfs:label "Advanced Python" ;
         ex:pubYear "2018"^^xsd:integer ;
         ex:sales "3000"^^xsd:integer ;
         ex:author ex:author1 ;
         ex:category "Programming" .

ex:book4 rdf:type ex:Book ;
         rdfs:label "Python for Data Science" ;
         ex:pubYear "2020"^^xsd:integer ;
         ex:sales "7000"^^xsd:integer ;
         ex:author ex:author3 ;
         ex:category "DataScience" .

ex:author1 rdf:type ex:Author ;
           ex:nationality "American" ;
           ex:award "Tech Excellence" .
ex:author2 rdf:type ex:Author ;
           ex:nationality "American" .
ex:author3 rdf:type ex:Author ;
           ex:nationality "American" .
""", format="turtle")

query = """
PREFIX ex: <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT REDUCED ?pubYear (SUM(?sales) AS ?totalSales)
WHERE {
    {
        SELECT ?book ?title ?pubYear ?sales ?author
        WHERE {
            ?book rdf:type ex:Book ;
                  rdfs:label ?title ;
                  ex:pubYear ?pubYear ;
                  ex:sales ?sales ;
                  ex:author ?author .
            ?author ex:nationality ?nationality .
            FILTER(?nationality = "American")
        }
    }
    {
        { ?book ex:category "Programming" }
        UNION
        { ?book ex:category "DataScience" }
    }
    MINUS {
        ?book ex:author ?author .
        ?author ex:award "Tech Excellence" .
    }
    FILTER(REGEX(?title, "python", "i"))
    OPTIONAL {
        ?author ex:award ?award .
    }
    BIND(?sales * 2 AS ?doubleSales)
    ?book ex:category ?category .
}
GROUP BY ?pubYear
HAVING(SUM(?sales) > 0)
ORDER BY DESC(?totalSales)
LIMIT 2 OFFSET 0
"""
stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["exampleEval"] = stage_extracter.customEval

results = g.query(query)
ZKPHandler(stage_extracter.get_stage_vals()).build()
# print(stage_extracter.get_stage_vals())
# for row in results:
#     print(f"Year: {row.pubYear}, Total Sales: {row.totalSales}")

# with open('stages.json', 'w') as fp:
#     json.dump(str(intermediate_results), fp)