from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF
import rdflib

bsbm = Namespace("http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/")
PRODUCT_GRAPH = URIRef("http://bsbm.org/graphs/products")
PRODUCER_GRAPH = URIRef("http://bsbm.org/graphs/producers")
REVIEW_GRAPH = URIRef("http://bsbm.org/graphs/reviews")

# Load your original data (e.g., .ttl file)
g = Graph()
g.parse("bsbm_light.nt")

# Create quads using a ConjunctiveGraph
cg = rdflib.ConjunctiveGraph()

for s, p, o in g:
    if (s, RDF.type, bsbm.Product) in g:
        cg.add((s, p, o, PRODUCT_GRAPH))
    elif (s, RDF.type, bsbm.Producer) in g:
        cg.add((s, p, o, PRODUCER_GRAPH))
    elif (s, RDF.type, bsbm.Review) in g:
        cg.add((s, p, o, REVIEW_GRAPH))
    else:
        # Default graph for unknown types
        cg.add((s, p, o, URIRef("http://bsbm.org/graphs/other")))

# Serialize to TRIG
cg.serialize(destination="bsbm_named_graphs.trig", format="trig")
