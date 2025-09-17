# ZKP-SPARQL: Zero Knowledge Proof for SPARQL

This project implements ZKP for SPARQL to support verifiable query processing when using SPARQL to retrieve and manipulate sensitive KG data stored in Resource Description Framework (RDF) format.

`shin-chiquito (https://github.com/thanhquanse/shin-chiquito.git)` is a framework to design ZKP circuits, and it requires an additional library `shin-zkp-sparql-plonkish (https://github.com/thanhquanse/shin-zkp-sparql-plonkish.git)` to support the plonkish backend. Therefore, it is required to install these two libraries.

## Usage

Go to [src/zkp-sparql] directory to freely run any py file with the names corresponding to the experiment you want to run. For example, we provide single operator's gate experiments like filter, orderby, etc or refer to `main_zkpsparql.py` for the entire experiment on multiple operator gates.