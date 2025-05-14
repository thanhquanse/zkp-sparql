#!/bin/bash

echo "##### Start experimenting the ZKP-SPARQL engine for 15 SPARQL queries #####"
echo
python main_engine.py >> ./logs/experiment.log 2>&1
echo "Done"

echo
echo

echo "##### Start experimenting the performance of SQL to SPARQL/Relational DBs to KG DBs #####"
echo
python main_sql2sparql.py >> ./logs/experiment.log 2>&1
echo "Done"