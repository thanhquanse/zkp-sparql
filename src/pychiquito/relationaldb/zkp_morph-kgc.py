import morph_kgc
import sqlite3
import csv

from rdflib import Graph

csv_dataset = './lineitem.tbl'
config_file = './config.ini'
sparql = """
PREFIX ex: <http://example.com/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?returnFlag ?lineStatus
       (SUM(?quantity) AS ?sum_qty)
       (SUM(?extendedPrice) AS ?sum_base_price)
       (SUM(?extendedPrice * (1 - ?discount)) AS ?sum_disc_price)
       (SUM(?extendedPrice * (1 - ?discount) * (1 + ?tax)) AS ?sum_charge)
       (AVG(?quantity) AS ?avg_qty)
       (AVG(?extendedPrice) AS ?avg_price)
       (AVG(?discount) AS ?avg_disc)
       (COUNT(?s) AS ?count_order)
WHERE {
  ?s a ex:LineItem ;
     ex:returnFlag ?returnFlag ;
     ex:lineStatus ?lineStatus ;
     ex:quantity ?quantity ;
     ex:extendedPrice ?extendedPrice ;
     ex:discount ?discount ;
     ex:tax ?tax ;
     ex:shipDate ?shipDate .
  FILTER (?shipDate <= "1998-08-03"^^xsd:date)
}
GROUP BY ?returnFlag ?lineStatus
ORDER BY ?returnFlag ?lineStatus
"""

sql = """
select
       l_returnflag,
       l_linestatus,
       sum(l_quantity) as sum_qty,
       sum(l_extendedprice) as sum_base_price,
       sum(l_extendedprice * (1-l_discount)) as sum_disc_price,
       sum(l_extendedprice * (1-l_discount) * (1+l_tax)) as sum_charge,
       avg(l_quantity) as avg_qty,
       avg(l_extendedprice) as avg_price,
       avg(l_discount) as avg_disc,
       count(*) as count_order
 from
       lineitem
 where
       l_shipdate <= date('1998-08-03')
 group by
       l_returnflag,
       l_linestatus
 order by
       l_returnflag,
       l_linestatus;
"""

def performSPARQL():
    graph: Graph = morph_kgc.materialize(config_file)
    results = graph.query(sparql)

    print("\n")
    print(f"Querying data from the graph DB with SPARQL...\n")
    for row in results:
        print(f'{row.returnFlag}, {row.lineStatus}, {row.sum_qty}, {row.sum_base_price}, {row.sum_disc_price}, {row.sum_charge}, {row.avg_qty}, {row.avg_price}, {row.avg_disc}, {row.count_order}')
    print("\n")

def createTable():
    conn = sqlite3.connect("lineitem.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lineitem (
            l_orderkey INTEGER,
            l_partkey INTEGER,
            l_suppkey INTEGER,
            l_linenumber INTEGER,
            l_quantity DECIMAL,
            l_extendedprice DECIMAL,
            l_discount DECIMAL,
            l_tax DECIMAL,
            l_returnflag CHAR(1),
            l_linestatus CHAR(1),
            l_shipdate DATE,
            l_commitdate DATE,
            l_receiptdate DATE,
            l_shipinstruct CHAR(25),
            l_shipmode CHAR(10),
            l_comment VARCHAR(44)
        )
    """)

    with open(csv_dataset, "r") as f:
        reader = csv.reader(f, delimiter=",")
        # Skip the header row (if present)
        headers = next(reader, None)
        # Prepare the INSERT query
        query = """
            INSERT INTO lineitem (
                l_orderkey, l_partkey, l_suppkey, l_linenumber, l_quantity,
                l_extendedprice, l_discount, l_tax, l_returnflag, l_linestatus,
                l_shipdate, l_commitdate, l_receiptdate, l_shipinstruct,
                l_shipmode, l_comment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Insert each row
        for row in reader:
            # Ensure the row has at least 16 columns (ignore l_dummy if present)
            if len(row) >= 16:
                cursor.execute(query, row[:16])

    conn.commit()
    conn.close()

def performSQL():
    conn = sqlite3.connect("lineitem.db")
    cursor = conn.cursor()

    print("\n")
    print(f"Querying data from the relational DB with SQL...\n")
    for row in cursor.execute(sql):
        print(row)
    print("\n")

if __name__ == "__main__":
    performSPARQL()
    print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    performSQL()