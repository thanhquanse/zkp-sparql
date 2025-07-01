import random
from argparse import ArgumentParser

def process_nt_file(input_file, output_paths):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    random.shuffle(lines)

    total = len(lines)
    pct_25 = lines[:total // 4]
    pct_50 = lines[:total // 2]

    with open(output_paths[0], 'w') as f:
        f.writelines(pct_25)
    with open(output_paths[1], 'w') as f:
        f.writelines(pct_50)

    print(f"Saved: {len(pct_25)} lines to {output_paths[0]}")
    print(f"Saved: {len(pct_50)} lines to {output_paths[1]}")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--dataset", type=str, default="swdf")
    input = parser.parse_args()

    input_path = f"./datasets/{input.dataset}/{input.dataset}.nt"
    output_paths = [f"./datasets/{input.dataset}/{input.dataset}_25_pct.nt", f"./datasets/{input.dataset}/{input.dataset}_50_pct.nt"]

    process_nt_file(input_path, output_paths)
