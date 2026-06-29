import csv
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD

# Namespaces (same as in earlier SPARQL)
SN   = Namespace("http://www.ldbc.eu/ldbc_socialnet/1.0/data/")
SNVOC = Namespace("http://www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/")

g = Graph()

# 1. File 1: Messages (text posts)
# id|creationDate|locationIP|browserUsed|content|length
with open("./message_fact/60k/comment.csv", "r") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        msg_id = row["id"]
        msg_uri = URIRef(f"{SN}msg{msg_id}")

        g.add((msg_uri, RDF.type, SNVOC.Message))
        g.add((msg_uri, SNVOC.creationDate, Literal(row["creationDate"], datatype=XSD.dateTime)))
        g.add((msg_uri, SNVOC.locationIP, Literal(row["locationIP"])))
        g.add((msg_uri, SNVOC.browserUsed, Literal(row["browserUsed"])))
        g.add((msg_uri, SNVOC.content, Literal(row["content"])))

        try:
            length_val = int(row["length"])
        except:
            length_val = None
        if length_val is not None:
            g.add((msg_uri, SNVOC.length, Literal(length_val, datatype=XSD.integer)))

# 2. File 2: Photos
# id|imageFile|creationDate|locationIP|browserUsed|language|content|length
with open("./message_fact/60k/post.csv", "r") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        photo_id = row["id"]
        photo_uri = URIRef(f"{SN}photo{photo_id}")

        g.add((photo_uri, RDF.type, SNVOC.Photo))
        g.add((photo_uri, SNVOC.imageFile, Literal(row["imageFile"])))
        g.add((photo_uri, SNVOC.creationDate, Literal(row["creationDate"], datatype=XSD.dateTime)))
        g.add((photo_uri, SNVOC.locationIP, Literal(row["locationIP"])))
        g.add((photo_uri, SNVOC.browserUsed, Literal(row["browserUsed"])))

        lang = row.get("language", "")
        if lang.strip():
            g.add((photo_uri, SNVOC.language, Literal(lang)))

        content = row.get("content", "").strip()
        if content:
            g.add((photo_uri, SNVOC.content, Literal(content)))

        try:
            length_val = int(row["length"])
        except:
            length_val = None
        if length_val is not None:
            g.add((photo_uri, SNVOC.length, Literal(length_val, datatype=XSD.integer)))

# 3. Serialize to Turtle
g.serialize(destination="msg_fact_sample.ttl", format="turtle")
print(f"Converted {len(g)} triples to msg_fact_sample.ttl")