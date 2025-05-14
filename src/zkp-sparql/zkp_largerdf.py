import rdflib
from memory_profiler import profile
from rdflib import Graph
from libs.stageextracter import StageExtracter
from libs.singlehandler import ZKPSingleHandler

g = Graph()

data = "./datasets/largerdfbench_drugbank_dump.nt"

query_1 = """
SELECT $drug $melt WHERE {
    { $drug <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugbank/meltingPoint> $melt. }
    UNION
    { $drug <http://dbpedia.org/ontology/Drug/meltingPoint> $melt . }
}
"""

query_2 = """
SELECT ?predicate ?object WHERE {
    { <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugs/DB00201> ?predicate ?object . }
    UNION    
    { <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugs/DB00201> <http://www.w3.org/2002/07/owl#sameAs> ?caff .
      ?caff ?predicate ?object . } 
}
"""

query_3 = """
SELECT ?Drug ?IntDrug ?IntEffect WHERE {
    ?y <http://www.w3.org/2002/07/owl#sameAs> ?Drug .
    ?Int <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugbank/interactionDrug1> ?y .
    ?Int <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugbank/interactionDrug2> ?IntDrug .
    ?Int <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugbank/text> ?IntEffect . 
}
"""

query_4 = """
SELECT $drug $transform $mass WHERE {  
 	{ $drug <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugbank/affectedOrganism>  'Humans and other mammals'.
 	  $drug <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugbank/casRegistryNumber> $cas .
 	} .
 	OPTIONAL { $drug <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugbank/biotransformation> $transform . } 
}
"""
complex_query_1 = """
PREFIX drugbank: <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugbank/> 
PREFIX drugtype: <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugtype/>
PREFIX kegg: <http://bio2rdf.org/ns/kegg#>
PREFIX chebi: <http://bio2rdf.org/ns/bio2rdf#>
PREFIX purl: <http://purl.org/dc/elements/1.1/>
SELECT DISTINCT ?drug	?drugDesc ?molecularWeightAverage 	?compound   ?ReactionTitle    ?ChemicalEquation 
WHERE
{
?drug 			drugbank:description 	 ?drugDesc .
?drug 			drugbank:drugType 	 drugtype:smallMolecule .
?drug 	     drugbank:keggCompoundId ?compound. 
OPTIONAL 
{ 
    ?drug drugbank:molecularWeightAverage ?molecularWeightAverage.
    FILTER (?molecularWeightAverage > 114) 
    }
}
LIMIT 1000
"""

complex_query_2 = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX drugbank: <http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugbank/>
PREFIX kegg: <http://bio2rdf.org/ns/kegg#>
PREFIX chebi: <http://bio2rdf.org/ns/chebi#>
PREFIX purl: <http://purl.org/dc/elements/1.1/>
PREFIX bio2RDF: <http://bio2rdf.org/ns/bio2rdf#>
SELECT ?drug ?keggmass ?chebiIupacName 
WHERE 
{
    ?drug rdf:type drugbank:drugs .
    ?drug drugbank:keggCompoundId ?keggDrug .
    ?keggDrug bio2RDF:mass ?keggmass .
    ?drug drugbank:genericName ?drugBankName .
    ?chebiDrug purl:title ?drugBankName .
    ?chebiDrug chebi:iupacName ?chebiIupacName .
    OPTIONAL { 
        ?drug drugbank:inchiIdentifier ?drugbankInchi .
        ?chebiDrug bio2RDF:inchi ?chebiInchi.
        FILTER (?drugbankInchi = ?chebiInchi) 
    }
}
"""

g.parse(data)
print(f"Loaded graph: {len(g)}")

@profile
def func():
    stage_extracter = StageExtracter()
    rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = stage_extracter.ZKPQueryEval

    results = g.query(complex_query_1)
    ZKPSingleHandler(stage_extracter.get_stage_vals()).build()

if __name__ == '__main__':
    func()