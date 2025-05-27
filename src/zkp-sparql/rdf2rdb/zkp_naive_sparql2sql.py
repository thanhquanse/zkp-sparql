import time
import sqlite3
import os
from rdflib import Graph
from memory_profiler import profile
from functools import wraps

# Parse RDF file (.nt or .ttl)
data = "../datasets/swdf/swdf.nt"
db = "../datasets/swdf/swdf.db"
dbtxt = "../datasets/swdf/swdf.txt"

sql = """
WITH PersonTriples AS (
    SELECT t2.subject AS instance, t2.predicate AS p, t2.object AS o,
           ROW_NUMBER() OVER (PARTITION BY t2.subject ORDER BY t2.predicate, t2.object) AS rn
    FROM triples t1
    JOIN triples t2 ON t1.subject = t2.subject
    WHERE t1.predicate = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
      AND t1.object = 'http://xmlns.com/foaf/0.1/Person'
)
SELECT DISTINCT instance, p, o, count(*) as countVal
FROM PersonTriples
WHERE o = 'Science Commons'
GROUP BY instance
ORDER BY instance, p, o
LIMIT 10;
"""

sql_export_query = """
WITH PersonTriples AS (
    SELECT t2.subject AS instance, t2.predicate AS p, t2.object AS o,
            ROW_NUMBER() OVER (PARTITION BY t2.subject ORDER BY t2.predicate, t2.object) AS rn
    FROM triples t1
    JOIN triples t2 ON t1.subject = t2.subject
    WHERE t1.predicate = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
        AND t1.object = 'http://xmlns.com/foaf/0.1/Person'
)
SELECT instance, p, o
FROM PersonTriples
WHERE rn = 1
"""

sparql = """
PREFIX  owl:  <http://www.w3.org/2002/07/owl#>
PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  foaf: <http://xmlns.com/foaf/0.1/>

SELECT DISTINCT  ?instance ?p ?o
WHERE
  { ?instance <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://xmlns.com/foaf/0.1/Person> .
    ?instance ?p ?o
  }
GROUP BY ?instance
ORDER BY ?instance ?p ?o
OFFSET  1000
LIMIT   10
"""

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result
    return timeit_wrapper

@timeit
def convert2rdb(gdb, rdb):
    g = Graph()
    g.parse(gdb)  # or format="nt" for N-Triples

    print(f"Converting the SWDF graph data with size: {len(g)}...\n")
    # Connect to SQLite database
    conn = sqlite3.connect(rdb)
    cursor = conn.cursor()

    # Create a table for triples
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS triples (
            subject,
            predicate,
            object
        )
    """)

    # Insert triples into the table
    for s, p, o in g:
        cursor.execute("INSERT INTO triples (subject, predicate, object) VALUES (?, ?, ?)", (str(s), str(p), str(o)))

    # Commit and close
    conn.commit()
    conn.close()

@timeit
def performSQLQuery(sql):
    print(f"Querying data from the relational DB with SQL...\n")
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    for row in cursor.execute(sql):
        print(row)
    print("\n")

@timeit
def performSPARQLQuery(sparql):
    print(f"Querying data from the graph DB with SPARQL...\n")
    g = Graph()
    g.parse(data)
    results = g.query(sparql)
    for row in results:
       print(f"{row.instance}, {row.p}, {row.o}")
    print("\n")

def export2file(db_file, output_file, limit=None, offset=None):
    # Check if database file exists
    if not os.path.exists(db_file):
        print(f"Error: Database file '{db_file}' not found")
        return
    
    sql_query = sql_export_query
    # Add LIMIT and OFFSET if specified
    if limit is not None:
        sql_query += f" LIMIT {limit}"
    if offset is not None:
        sql_query += f" OFFSET {offset}"

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Execute query
        cursor.execute(sql_query)
        
        # Open output file
        with open(output_file, "w", encoding="utf-8") as f:
            # Fetch and write rows
            for row in cursor:
                # Join row values with '|' and escape any '|' in the data
                formatted_row = "|".join(str(value).replace("|", "\\|") for value in row)
                f.write(formatted_row + "\n")

        print(f"Data exported successfully to '{output_file}'")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except IOError as e:
        print(f"File error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # convert2rdb(data, db)
    # export2file(db, dbtxt)
    performSQLQuery(sql)
    # print("----------------------------------------------------------------------------------------------------------------------------------------------------------------")
    # performSPARQLQuery(sparql)