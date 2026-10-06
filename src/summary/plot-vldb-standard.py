import os
import re
from argparse import ArgumentParser

import matplotlib

# Use a non-interactive backend (safe on servers) and embed TrueType (Type 42)
# fonts instead of Type 3. Must be set before any figure is created.
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

# Optional: match the paper's font (Libertinus). Falls back to DejaVu Serif
# if Libertinus is not installed. Set USE_SERIF_FONT = False to keep the default.
USE_SERIF_FONT = False
if USE_SERIF_FONT:
    matplotlib.rcParams["font.family"] = "serif"
    matplotlib.rcParams["font.serif"] = ["Libertinus Serif", "DejaVu Serif"]

import matplotlib.pyplot as plt
import pandas as pd

OUT_DIR = "./vldb-plots"

dict_size: dict = {
    "swdf": 304583,
    "bsbm": 350062,
    "drugbank": 766920,
    "bsbm_compared": "~50000",
    "zkgraph": 60000,
}

dict_unit: dict = {
    "Running Time": "s",
    "Memory": "GB",
    "Proof Verification Time": "s",
    "Proof Size": "KB",
    "Total Proof Gen": "s",
}


def extract_info(file_path, output_path):
    with open(file_path, "r") as f:
        content = f.read()

    pattern = re.compile(
        r"-+ Experimenting: (\w+) - .*/(\w+\.sparql) -+\s+"
        r".*?Params: \{.*?\"k\": (\d+).*?\}\s+"
        r".*?Number of query results: (\d+)\s+"
        r".*?Query execution time: ([\d.]+)\s+"
        r".*?Time to generate proof ([\d.]+)s\s+"
        r".*?Time to verify proof ([\d.]+)s\s+"
        r".*?Proving time: ([\d.]+)",
        re.DOTALL,
    )

    data = []
    for match in pattern.findall(content):
        dataset, query, k, num_results, query_time, proof_gen_time, verify_time, proving_time = match
        data.append({
            "Dataset": dataset,
            "Query": query,
            "Param (k)": int(k),
            "Num Query Results": int(num_results),
            "Query Execution Time (s)": float(query_time),
            "Proving Time (s)": float(proving_time),
            "Time to Generate Proof (s)": float(proof_gen_time),
            "Time to Verify Proof (s)": float(verify_time),
        })

    pd.DataFrame(data).to_excel(output_path, index=False)
    print(f"Extracted data saved to {output_path}")


def parse_experiment_blocks(file_path, output_path):
    with open(file_path, "r") as f:
        content = f.read()

    blocks = re.findall(
        r"-{10,} Experimenting: (.+?) - .*?/(q\d+_.*?\.sparql) -+.*?INFO: Params: \{.*?\"k\": (\d+).*?\}.*?"
        r"Number of query results: (\d+).*?"
        r"Query execution time: ([\d.]+).*?"
        r"Time to generate proof ([\d.]+)[a-z]*.*?"
        r"Time to verify proof ([\d.]+)[a-z]*.*?"
        r"INFO: Proving time: ([\d.]+)",
        content,
        re.DOTALL,
    )

    rows = []
    for match in blocks:
        dataset, query, k, num_results, query_time, proof_gen_time, verify_time, proving_time = match
        rows.append({
            "Dataset": dataset.strip(),
            "Query": query.strip(),
            "Param (k)": int(k),
            "Num Query Results": int(num_results),
            "Query Execution Time (s)": float(query_time),
            "Time to Generate Proof (s)": float(proof_gen_time),
            "Time to Verify Proof (s)": float(verify_time),
            "Proving Time (s)": float(proving_time),
        })

    pd.DataFrame(rows).to_excel(output_path, index=False)


def plot_super_circuit_results(df: pd.DataFrame, sheet_name: str, col2plot: str):
    pivot_df = df.pivot(index="Query", columns="Dataset Size", values=col2plot)
    compared = sheet_name in ("bsbm_compared", "zkgraph")

    if compared:
        pivot_df.columns = [f"{col}" for col in pivot_df.columns]
        pivot_df = pivot_df[sorted(pivot_df.columns, reverse=True)]
    else:
        pivot_df.columns = [f"{col}%" for col in pivot_df.columns]

    fig, ax = plt.subplots(figsize=(4, 4))
    pivot_df = pivot_df.sort_index()
    pivot_df.plot(
        kind="bar",
        color=["blue", "orange", "grey"],
        width=(0.4 if compared else 0.9),
        ax=ax,
    )
    ax.legend(
        title=f"Full size: {dict_size[sheet_name]}",
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        frameon=False,
    )

    ax.set_ylabel(f"{col2plot} ({dict_unit[col2plot]})")
    ax.set_xlabel("")
    plt.xticks(rotation=0, ha="right")
    fig.tight_layout(rect=[0, 0, 1, 1])

    fig.savefig(f"{OUT_DIR}/plot_{sheet_name}_{col2plot}.pdf", format="pdf")
    plt.close(fig)


def plot_single_circuit_results(df: pd.DataFrame, sheet_name: str, col2plot: str):
    ax = df.plot(
        x="Gate",
        y="Running Time",
        kind="barh",
        figsize=(6, 2),
        color="lightslategray",
        legend=False,
    )

    ax.set_xlabel("Running Time (s)")
    ax.set_ylabel("")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)
    fig = ax.get_figure()
    fig.tight_layout()

    fig.savefig(f"{OUT_DIR}/plot_{sheet_name}_{col2plot}.pdf", format="pdf")
    plt.close(fig)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input_path", type=str,
                        default="./summary/experiment_2025-06-18_10-25-21.log")
    parser.add_argument("--output_path", type=str,
                        default="./experiment_official_results_revision.xlsx")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    # Uncomment to rebuild the Excel file from the log first:
    # parse_experiment_blocks(args.input_path, args.output_path)

    excel_file = args.output_path
    sheets = ["swdf", "bsbm", "drugbank", "bsbm_compared", "zkgraph"]
    columns = ["Running Time", "Memory", "Proof Verification Time", "Proof Size"]

    for sheet in sheets:
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            df = df.round(1)
        except Exception as e:
            print(f"Error loading Excel file or sheet: {e}")
            break

        for col in columns:
            if col not in df.columns:
                print(f"Column '{col}' not found in sheet. Available columns:\n{list(df.columns)}")
                break
            plot_super_circuit_results(df, sheet, col)

    single_df = pd.read_excel(excel_file, sheet_name="swdf_single_gate")
    single_df = single_df.round(1)
    plot_single_circuit_results(single_df, "swdf_single_gate", "Running Time")

    print("Done. Figures saved in", OUT_DIR)