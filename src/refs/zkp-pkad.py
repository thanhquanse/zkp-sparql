import argparse
import rdflib
import ast
import my_rust_module
from rdflib import Graph, Namespace, BNode
from rdflib.namespace import FOAF, RDF, RDFS
from rdflib.plugins.sparql.evaluate import evalBGP, evalFilter

prefix = "http://freebase-graph.insubria/anonymized/"
g = Graph()
g.parse("./freebase_full.ttl", format="turtle")
print(f"Loaded {len(g)} triples.")

freebase = Namespace(prefix)
g.bind("freebase", freebase)

# triples = []

inferred_sub_class = (
    RDFS.subClassOf * "*"  # type: ignore[operator]
)  # any number of rdfs.subClassOf

def read_sparql_template(dataset):
    sparql_path = f'./examples/sparql/{dataset}.spql'

    with open(sparql_path, 'r') as file:
        sql_query = file.read()

    return sql_query

def detect_k_values(dataset, item):
    values = []
    query = f"""
    PREFIX freebase: <http://freebase-graph.insubria/anonymized/>
    select ?input ?p ?o #(count(?o) as ?count)
    where {{
        # values ?input {{ freebase:user_francis_ii_holy_roman_emperor }} .
        ?input ?p ?o .
        FILTER(?input = freebase:user_francis_ii_holy_roman_emperor)
    }}
    """
    for r in g.query(query):
        values.append("|".join([r['input'].replace(prefix, ""), r['p'].replace(prefix, ""), r['o'].replace(prefix, "")]))
        # print("Results:", r['count'])
        # uri = ast.literal_eval(r)
        # print(r['input'])
        # pass

    return values

def customEval(ctx, part):  # noqa: N802
    """
    Rewrite triple patterns to get super-classes
    """
    if part.name == "BGP":
        # rewrite triples
        triples = []
        for t in part.triples:
            if t[1] == RDF.type:
                bnode = BNode()
                triples.append((t[0], t[1], bnode))
                triples.append((bnode, inferred_sub_class, t[2]))
            else:
                triples.append(t)

        # delegate to normal evalBGP
        return evalBGP(ctx, triples)

    raise NotImplementedError()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="freebase")
    parser.add_argument("--save_dir", type=str, default="./outputs/")
    args = parser.parse_args()

    rdflib.plugins.sparql.CUSTOM_EVALS["ZKPQueryEval"] = customEval

    condition = ["user_francis_ii_holy_roman_emperor"]
    triples = detect_k_values(args.dataset, "user_francis_ii_holy_roman_emperor")

    # print(triples)
    # result = my_rust_module.multiply(5, 3)
    # print(f"5 * 3 = {result}")

    # doubles = my_rust_module.count_doubles("rrusttt")
    # print(f"Doubled characters in 'rrusttt': {doubles}") 

    # check = my_rust_module.get_data("abc", "def")
    # print(f"Boolean: {check}")

    # triples = ["<apple>|<banana>|<cherry>", "<dog>|<cat>|<apple>", "<apple>|<blue>|<green>"]
    # condition = ["apple"]
    check = my_rust_module.zkp_pkad(triples, condition)
    print(f"Proof ok?: {check}")