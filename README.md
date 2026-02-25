# ZKP-SPARQL: Zero-Knowledge Proof for SPARQL

This project implements Zero-Knowledge Proofs (ZKP) for SPARQL to support verifiable query processing when retrieving and manipulating sensitive Knowledge Graph (KG) data stored in Resource Description Framework (RDF) format.

## Table of Contents

- [Overview](#overview)
- [Environment Setup](#environment-setup)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Used Hardware](#used-hardware)
- [Citation](#citation)

## Overview

ZKP-SPARQL enables privacy-preserving SPARQL queries over sensitive RDF data by leveraging zero-knowledge proof systems. This ensures that query results can be verified without exposing the underlying data or query parameters.

## Environment Setup

### Prerequisites

| Dependency | Version | Installation |
|------------|---------|--------------|
| Rust | 1.83+ | [rust-lang.org](https://rust-lang.org/tools/install/) |
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| PyO3 | — | [pyo3.rs](https://pyo3.rs/v0.28.2/index.html) |

Verify your Rust installation:
```sh 
rustc --version
```

### Step 1: Python Virtual Environment
Create and activate a virtual environment:
```sh
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 2: Install Build Tools
Install Maturin (for PyO3-based builds):
```sh
pip install maturin
```
For more details, see the [Maturin documentation](https://www.maturin.rs/installation.html) or [PyO3 Getting Started](https://pyo3.rs/main/getting-started).

### Step 3: Install ZKP Chiquito Dependency
Clone and build our redesigned Chiquito framework (required for ZKP functionality):
```sh
wget -O zkpchiquito.zip https://anonymous.4open.science/api/repo/chiquito-9B54/zip
unzip zkpchiquito.zip -d ./path/to/zkpchiquito
cd ./path/to/zkpchiquito

# Ensure virtual environment is activated
pip install -r requirements.txt
maturin develop
```
**Note:** This redesigned Chiquito requires a specific Plonkish backend defined in its Cargo.toml, which includes bug fixes tailored to ZKP-SPARQL. If using a different backend, ensure full compatibility.

## Installation
Clone ZKP-SPARQL Repository
```sh
git clone https://github.com/thanhquanse/zkp-sparql.git
cd zkp-sparql
pip install -r requirements.txt
```

## Project Structure
```sh
zkp-sparql
├── src
│   ├── datasets              # Experimental datasets
│   ├── enums                 # Enumeration definitions
│   ├── gates                 # ZKP gate implementations
│   ├── libs                  # Supporting libraries
│   ├── rdb2rdf               # RDB-to-RDF transformation resources (ref only)
│   ├── rdf2rdb               # RDF-to-RDB transformation resources
│   ├── report                # Experiment results and reports
│   ├── utils                 # Common utility functions
│   ├── main.py               # Main python script to run the experiment
│   ├── run.sh                # Bash script to the main script in one shot
│   ├── zkp_project.py        # Single ZKP experiment for Project operator
│   ├── zkp_filter.py         # Single ZKP experiment for Filter operator
│   ├── zkp_union.py          # Single ZKP experiment for Union operator
│   ├── zkp_limit.py          # Single ZKP experiment for Limit operator
│   └── ...                   # Single ZKP experiment for other operators
├── requirements.txt          # Python dependencies
└── README.md
```

## Used Hardware
Experiments were conducted on Chameleon Cloud Skylake nodes with:
- Dual Intel Xeon Skylake CPUs @ 2.60 GHz
- 192 GB RAM
- 10 Gigabit Ethernet connectivity

## Dataset
Due to size limitation, full datasets are commited in another drive storage:
- [SWDF](https://drive.google.com/drive/folders/1DlnMrFvxMcG4Ikt3b-aeHgj0g6T0z7h7?usp=sharing)
- [BSBM](https://drive.google.com/drive/folders/1BWiFoYNrJgVScD7rDvcJCPAlwiT2ale4?usp=sharing)
- [Drugbank](https://drive.google.com/drive/folders/1vbN63pTRxf1uFax4MCPju30KO78Lz2mf?usp=sharing)

Or refer to [here](http://wbsg.informatik.uni-mannheim.de/bizer/berlinsparqlbenchmark/spec/Dataset/index.html) and [here](https://github.com/blazegraph/database/wiki/BSBM) to have more details about the synthetic dataset as well as generate it if needed.

Download them and put in the appropriate sub-directories under `datasets` directory

## Usage
**Single Operator Experiments**

Individual operator gates are available as zkp_\<operator\>.py files. These demonstrate specific SPARQL operators with sample RDF data and queries.

***Available operators:***

- zkp_project.py: Project operations
- zkp_union.py: Union operations
- zkp_filter.py: Filter operations
- (and others)

***Example:***
```sh
python zkp_union.py
```
**Note:** You can modify the demo data and queries, but ensure query-RDF compatibility.

***Full Benchmark Experiments***

Run comprehensive benchmarks (Q1–Q5 across proportions of three datasets):
```sh
bash run.sh
```
**Experiments included:**
- Benchmarking queries Q1–Q5 on proportionally divided datasets
- Performance comparison: PoneglyphDB vs. ZKP-SPARQL
- Gate-level breakdown measurements

**Tip:** Edit main.py to exclude specific experiments as needed.

## Citation