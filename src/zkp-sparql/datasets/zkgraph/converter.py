# import csv
# from rdflib import Graph, Namespace, Literal, URIRef
# from rdflib.namespace import RDF, XSD, FOAF

# # Namespaces (extend with http://www.ldbcouncil.org/ldbc_snb# for full LDBC)
# LDBC = Namespace("http://www.ldbcouncil.org/ldbc_snb#")
# BASE = "http://example.org/"

# g = Graph()

# # File 1: Persons
# with open('./person_fact/60k/person_0_0.csv', 'r') as f:
#     reader = csv.DictReader(f, delimiter='|')
#     for row in reader:
#         person_id = row['id']
#         subj = URIRef(f"{BASE}person/{person_id}")
#         g.add((subj, RDF.type, LDBC.Person))
#         g.add((subj, FOAF.firstName, Literal(row['firstName'])))
#         g.add((subj, FOAF.lastName, Literal(row['lastName'])))
#         g.add((subj, LDBC.gender, Literal(row['gender'])))
#         g.add((subj, LDBC.birthday, Literal(row['birthday'], datatype=XSD.date)))
#         g.add((subj, LDBC.creationDate, Literal(row['creationDate'], datatype=XSD.dateTime)))
#         g.add((subj, LDBC.locationIP, Literal(row['locationIP'])))
#         g.add((subj, LDBC.browserUsed, Literal(row['browserUsed'])))

# # File 2: Knows relations
# with open('./person_fact/60k/person_knows_person_0_0.csv', 'r') as f:
#     reader = csv.DictReader(f, delimiter='|')
#     for row in reader:
#         src_id = row['Person.id']  # First column
#         dst_id = row['Person.id_1']  # Second column (adjust if named differently)
#         subj = URIRef(f"{BASE}person/{src_id}")
#         obj = URIRef(f"{BASE}person/{dst_id}")
#         g.add((subj, LDBC.knows, obj))
#         g.add((subj, LDBC.knowsCreationDate, Literal(row['creationDate'], datatype=XSD.dateTime)))

# # Serialize to Turtle
# g.serialize(destination='./snb_sample.ttl', format='turtle')
# print("Converted to snb_sample.ttl")

import csv
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD

SN = Namespace("http://www.ldbc.eu/ldbc_socialnet/1.0/data/")
SNVOC = Namespace("http://www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/")
g = Graph()

# File 1: Persons (add snvoc:hasPerson self-links for query compatibility)
with open('./person_fact/60k/person_0_0.csv', 'r') as f:
    reader = csv.DictReader(f, delimiter='|')
    for row in reader:
        pid = row['id']
        person_uri = URIRef(f"{SN}pers{pid}")
        g.add((person_uri, RDF.type, SNVOC.Person))  # Assume Person class
        g.add((person_uri, SNVOC.hasPerson, person_uri))  # Self-link for query pattern
        g.add((person_uri, SNVOC.firstName, Literal(row['firstName'])))
        g.add((person_uri, SNVOC.lastName, Literal(row['lastName'])))
        g.add((person_uri, SNVOC.gender, Literal(row['gender'])))
        g.add((person_uri, SNVOC.birthday, Literal(row['birthday'], datatype=XSD.date)))
        g.add((person_uri, SNVOC.creationDate, Literal(row['creationDate'], datatype=XSD.dateTime)))
        g.add((person_uri, SNVOC.locationIP, Literal(row['locationIP'])))
        g.add((person_uri, SNVOC.browserUsed, Literal(row['browserUsed'])))

# File 2: Knows (add forward snvoc:knows + reverse snvoc:hasPerson)
with open('./person_fact/60k/person_knows_person_0_0.csv', 'r') as f:
    reader = csv.DictReader(f, delimiter='|')
    for row in reader:
        src_id = row['Person.id']  # src
        dst_id = row['Person.id_1']  # dst (Person.id_1 or similar)
        src_uri = URIRef(f"{SN}pers{src_id}")
        dst_uri = URIRef(f"{SN}pers{dst_id}")
        g.add((src_uri, SNVOC.knows, dst_uri))
        g.add((dst_uri, SNVOC.hasPerson, src_uri))  # Reverse for bidirectional query
        g.add((src_uri, SNVOC.knowsCreationDate, Literal(row['creationDate'], datatype=XSD.dateTime)))
        # Or link creationDate to knows node if reified: g.add((src_uri, SNVOC.knowsCreationDate, knows_node))

g.serialize(destination='snb_sample.ttl', format='turtle')
print("Converted to snb_sample.ttl - SPARQL ready!")