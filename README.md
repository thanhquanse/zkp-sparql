# ZKP-SPARQL: Zero Knowledge Proof for SPARQL

This project implements ZKP for SPARQL to support verifiable query processing when using SPARQL to retrieve and manipulate sensitive KG data stored in Resource Description Framework (RDF) format.
 
## Installation

We recommend using a virtual environment with Python 3.10, with the required packages that can be installed via `pip install -r requirements.txt` command

## Hardware used for experiments

The Chameleon Cloud with a Skylake node configured with dual Intel Xeon Skylake CPUs, at 2.60 GHz, 192 GB of RAM, and 10 Gigabit Ethernet connectivity.

## Project structure

    .
    ├── src
    ├──── ref                   # Additional modules to support the development for reference only
    ├─────── ...     
    ├── zkp-sparql              # Main directory
    ├──── datasets              # Datasets used for experiments
    ├─────── ... 
    ├──── enums                 # Enums
    ├──── gates                 # Main gate designs
    ├─────── ... 
    ├──── libs                  # Libaries used for experiments
    ├─────── ... 
    ├──── rdb2rdf               # Resources for rdb to rdf transformation to compare zkp-sparql with the naive way
    ├─────── ... 
    ├──── rdf2rdb               # Resources for rdf to rdb transformation to compare zkp-sparql with the naive way
    ├─────── ... 
    ├──── report                # Experiment report folder
    ├──── utils
    ├─────── ... 
    └── requirements.txt        # List of packages must be installed for the experiments
    └── README.md

## Usage

Go to [src/zkp-sparql] directory to freely run any py file with the names corresponding to the experiment you want to run. For example, we provide single operator's gate experiments like filter, orderby, etc or refer to `main_zkpsparql.py` for the entire experiment on multiple operator gates.