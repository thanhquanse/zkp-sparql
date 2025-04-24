import rdflib
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler

g = Graph()

data = "./datasets/bsbm_dataset_update.nt"

query_1 = """
PREFIX bsbm-inst: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/instances/>
PREFIX bsbm: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/vocabulary/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?product ?label
WHERE { 
    ?product rdfs:label ?label .
    ?product a bsbm-inst:ProductType2 .
    ?product bsbm:productFeature bsbm-inst:ProductFeature7 . 
    ?product bsbm:productFeature bsbm-inst:ProductFeature338 . 
    ?product bsbm:productPropertyNumeric1 ?value1 . 
    FILTER (?value1 > 100) 
}
ORDER BY ?label
LIMIT 2
"""

query_2 = """
SELECT ?label ?comment ?producer ?productFeature ?propertyTextual1 ?propertyTextual2 ?propertyTextual3
 ?propertyNumeric1 ?propertyNumeric2 ?propertyTextual4 ?propertyTextual5 ?propertyNumeric4 
WHERE {
    VALUES ?input { bsbm-inst:Product1002 }
    bsbm-inst:Product1002 rdfs:label ?label .
    bsbm-inst:Product1002 rdfs:comment ?comment .
    bsbm-inst:Product1002 bsbm:producer ?p .
    ?p rdfs:label ?producer .
    bsbm-inst:Product1002 dc:publisher ?p . 
    bsbm-inst:Product1002 bsbm:productFeature ?f .
    ?f rdfs:label ?productFeature .
    bsbm-inst:Product1002 bsbm:productPropertyTextual1 ?propertyTextual1 .
    bsbm-inst:Product1002 bsbm:productPropertyTextual2 ?propertyTextual2 .
    bsbm-inst:Product1002 bsbm:productPropertyTextual3 ?propertyTextual3 .
    bsbm-inst:Product1002 bsbm:productPropertyNumeric1 ?propertyNumeric1 .
    bsbm-inst:Product1002 bsbm:productPropertyNumeric2 ?propertyNumeric2 .
    OPTIONAL { bsbm-inst:Product1002 bsbm:productPropertyTextual4 ?propertyTextual4 }
    OPTIONAL { bsbm-inst:Product1002 bsbm:productPropertyTextual5 ?propertyTextual5 }
    OPTIONAL { bsbm-inst:Product1002 bsbm:productPropertyNumeric4 ?propertyNumeric4 }
}
"""

query_3 = """
PREFIX bsbm-inst: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/instances/>
PREFIX bsbm: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/vocabulary/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT ?product ?label
WHERE {
    ?product rdfs:label ?label .
    ?product a bsbm-inst:ProductType2 .
	?product bsbm:productFeature bsbm-inst:ProductFeature7 .
	?product bsbm:productPropertyNumeric1 ?p1 .
	FILTER ( ?p1 > 10 ) 
	?product bsbm:productPropertyNumeric3 ?p3 .
	FILTER (?p3 < 500 )
    OPTIONAL { 
        ?product bsbm:productFeature bsbm-inst:ProductFeature338 .
        ?product rdfs:label ?testVar }
    FILTER (!bound(?testVar)) 
}
ORDER BY ?label
LIMIT 30
"""

query_4 = """
PREFIX bsbm-inst: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/instances/>
PREFIX bsbm: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/vocabulary/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT DISTINCT ?product ?label ?propertyTextual
WHERE {
    { 
       ?product rdfs:label ?label .
       ?product rdf:type bsbm-inst:ProductType2 .
       ?product bsbm:productFeature bsbm-inst:ProductFeature7 .
	   ?product bsbm:productFeature bsbm-inst:ProductFeature3 .
       ?product bsbm:productPropertyTextual1 ?propertyTextual .
	   ?product bsbm:productPropertyNumeric1 ?p1 .
	   FILTER ( ?p1 > 5 )
    } 
    UNION 
    {
       ?product rdfs:label ?label .
       ?product rdf:type bsbm-inst:ProductType10 .
       ?product bsbm:productFeature bsbm-inst:ProductFeature4 .
	   ?product bsbm:productFeature bsbm-inst:ProductFeature16 .
       ?product bsbm:productPropertyTextual1 ?propertyTextual .
	   ?product bsbm:productPropertyNumeric2 ?p2 .
	   FILTER ( ?p2 > 10 ) 
    } 
}
ORDER BY ?label
OFFSET 5
LIMIT 10
"""

query_5 = """
PREFIX bsbm-inst: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/instances/>
PREFIX bsbm: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/vocabulary/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT DISTINCT ?product ?productLabel
WHERE { 
	?product rdfs:label ?productLabel .
    FILTER (bsbm-inst:Product2000 != ?product)
	bsbm-inst:Product1095 bsbm:productFeature ?prodFeature .
	?product bsbm:productFeature ?prodFeature .
	bsbm-inst:Product1095 bsbm:productPropertyNumeric1 ?origProperty1 .
	?product bsbm:productPropertyNumeric1 ?simProperty1 .
	FILTER (?simProperty1 < (?origProperty1 + 120) && ?simProperty1 > (?origProperty1 - 120))
	bsbm-inst:Product1095 bsbm:productPropertyNumeric2 ?origProperty2 .
	?product bsbm:productPropertyNumeric2 ?simProperty2 .
	FILTER (?simProperty2 < (?origProperty2 + 170) && ?simProperty2 > (?origProperty2 - 170))
}
ORDER BY ?productLabel
LIMIT 5
"""

query_6 = """
PREFIX bsbm-inst: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/instances/>
PREFIX bsbm: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/vocabulary/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT ?product ?label
WHERE {
	?product rdfs:label ?label .
    ?product rdf:type bsbm:Product .
	FILTER regex(?label, "a", "i")
}
"""

query_7 = """
PREFIX bsbm-inst: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/instances/>
PREFIX bsbm: <http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/vocabulary/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX rev: <http://purl.org/stuff/rev#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?productLabel ?offer ?price ?vendor ?vendorTitle ?review ?revTitle 
       ?reviewer ?revName ?rating1 ?rating2
WHERE { 
	bsbm-inst:dataFromProducer22/Product1004 rdfs:label ?productLabel . 	
    OPTIONAL {
        ?offer bsbm:product bsbm-inst:dataFromProducer22/Product1004.
		?offer bsbm:price ?price .
		?offer bsbm:vendor ?vendor .
		?vendor rdfs:label ?vendorTitle .
        ?vendor bsbm:country <http://downlode.org/rdf/iso-3166/countries#DE> .
        ?offer dc:publisher ?vendor . 
        ?offer bsbm:validTo ?date .
        FILTER (?date > "2019-03-24" )
    }
    OPTIONAL {
	?review bsbm:reviewFor bsbm-inst:dataFromProducer22/Product1004 .
	?review rev:reviewer ?reviewer .
	?reviewer foaf:name ?revName .
	?review dc:title ?revTitle .
    OPTIONAL { ?review bsbm:rating1 ?rating1 . }
    OPTIONAL { ?review bsbm:rating2 ?rating2 . } 
    }
}
"""

stage_extracter = StageExtracter()
rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

g.parse(data)
print(f"Loaded graph: {len(g)}")
results = g.query(query_6)
ZKPSingleHandler(stage_extracter.get_stage_vals()).build()