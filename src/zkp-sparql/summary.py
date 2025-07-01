import re
import pandas as pd
import pandas as pd
import matplotlib.pyplot as plt
from argparse import ArgumentParser

dict_size: dict = {
    "swdf": 304583,
    "bsbm": 350062,
    "drugbank": 766920,
    "bsbm_compared": 50000
}

dict_unit: dict = {
    "Running Time": "s",
    "Memory": "GB",
    "Proof Verification Time": "s",
    "Proof Size": "KB"
}

def extract_info(file_path, output_path):
    with open(file_path, 'r') as f:
        content = f.read()

    pattern = re.compile(
        r"-+ Experimenting: (\w+) - .*/(\w+\.sparql) -+\s+"
        r".*?Params: \{.*?\"k\": (\d+).*?\}\s+"
        r".*?Number of query results: (\d+)\s+"
        r".*?Query execution time: ([\d.]+)\s+"
        r".*?Time to generate proof ([\d.]+)s\s+"
        r".*?Time to verify proof ([\d.]+)s\s+"
        r".*?Proving time: ([\d.]+)",
        re.DOTALL
    )

    matches = pattern.findall(content)

    # Prepare data for DataFrame
    data = []
    for match in matches:
        dataset, query, k, num_results, query_time, proof_gen_time, verify_time, proving_time = match
        data.append({
            "Dataset": dataset,
            "Query": query,
            "Param (k)": int(k),
            "Num Query Results": int(num_results),
            "Query Execution Time (s)": float(query_time),
            "Proving Time (s)": float(proving_time),
            "Time to Generate Proof (s)": float(proof_gen_time),
            "Time to Verify Proof (s)": float(verify_time)
        })

    # Save to Excel
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    print(f"Extracted data saved to {output_path}")

def parse_experiment_blocks(file_path, output_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Split content into experiment blocks
    blocks = re.findall(
        r"-{10,} Experimenting: (.+?) - .*?/(q\d+_.*?\.sparql) -+.*?INFO: Params: \{.*?\"k\": (\d+).*?\}.*?"
        r"Number of query results: (\d+).*?"
        r"Query execution time: ([\d.]+).*?"
        r"Time to generate proof ([\d.]+)[a-z]*.*?"
        r"Time to verify proof ([\d.]+)[a-z]*.*?"
        r"INFO: Proving time: ([\d.]+)",
        content,
        re.DOTALL
    )

    # Convert blocks into structured data
    rows = []
    for match in blocks:
        dataset, query, k, num_results, query_time, proof_gen_time, verify_time, proving_time = match

        row = {
            "Dataset": dataset.strip(),
            "Query": query.strip(),
            "Param (k)": int(k),
            "Num Query Results": int(num_results),
            "Query Execution Time (s)": float(query_time),
            "Time to Generate Proof (s)": float(proof_gen_time),
            "Time to Verify Proof (s)": float(verify_time),
            "Proving Time (s)": float(proving_time),
        }
        rows.append(row)

    pd.DataFrame(rows).to_excel(output_path, index=False)

def plot_super_circuit_results(df: pd.DataFrame, sheet_name: str, col2plot: str):
    pivot_df = df.pivot(index='Query', columns='Dataset Size', values=col2plot)
    
    if sheet_name == "bsbm_compared":
        pivot_df.columns = [f"{col}" for col in pivot_df.columns]
        pivot_df = pivot_df[sorted(pivot_df.columns, reverse=True)]
    else:
        pivot_df.columns = [f"{col}%" for col in pivot_df.columns]

    fig, ax = plt.subplots(figsize=(4, 4))
    pivot_df = pivot_df.sort_index()
    pivot_df.plot(kind='bar', figsize=(4, 4), color=['blue', 'orange', 'grey'], width=0.9, ax=ax)
    ax.legend(title=f'Full size: {dict_size[sheet_name]}', loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=3, frameon=False)
    # ax = pivot_df.plot(kind='bar', figsize=(4, 4), color=['blue', 'orange', 'grey'], width=0.4)

    # for container in ax.containers:
    #     ax.bar_label(container, label_type='edge', rotation=0)

    plt.ylabel(f"{col2plot} ({dict_unit[col2plot]})")
    plt.xlabel("")
    plt.xticks(rotation=0, ha='right')
    plt.tight_layout(rect=[0, 0, 1, 1])
    # plt.grid(True, axis='y', linestyle='--', alpha=0.7)

    # plt.legend(title=f'Full size: {dict_size[sheet_name]}')
    plt.savefig(f"./summary/plot_{sheet_name}_{col2plot}.png")
    plt.close()

def plot_single_circuit_results(df: pd.DataFrame, sheet_name: str, col2plot: str):
    df.plot(
        x="Gate",
        y="Running Time",
        kind="barh",
        figsize=(6, 2),
        color="grey",
        legend=False
    )

    plt.xlabel("Running Time (s)")
    plt.ylabel("")
    # plt.legend(title="")
    # plt.title("Gate Execution Time")
    plt.tight_layout()
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.grid(True, axis='x', linestyle='--', alpha=0.5)

    plt.savefig(f"./summary/plot_{sheet_name}_{col2plot}.png")
    plt.close()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input_path", type=str, default="./summary/experiment_2025-06-18_10-25-21.log")
    parser.add_argument("--output_path", type=str, default="./summary/experiment_excel_official_results_v2.xlsx")
    input = parser.parse_args()

    # Run the function with your log file
    # parse_experiment_blocks(input.input_path, input.output_path)

    excel_file = input.output_path
    sheets = ['swdf', 'bsbm', 'drugbank', 'bsbm_compared']
    columns = ['Running Time', 'Memory', 'Proof Verification Time', 'Proof Size']

    for sheet in sheets:
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            df = df.round(1)
        except Exception as e:
            print(f"Error loading Excel file or sheet: {e}")
            break
        
        for col in columns:
            # Check if the selected column exists
            if col not in df.columns:
                print(f"Column '{col}' not found in sheet. Available columns:\n{list(df.columns)}")
                break
            plot_super_circuit_results(df, sheet, col)

    # single_df = pd.read_excel(excel_file, sheet_name="swdf_single_gate")
    # single_df = single_df.round(1)
    # plot_single_circuit_results(single_df, "swdf_single_gate", "Running Time")