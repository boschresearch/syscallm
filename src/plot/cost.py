import re
import os
import sys
from collections import defaultdict
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config as config

# ---- CONFIG ----
data_dir = config.data_dir
file_path = f"{data_dir}/gpt5.2.11886253.stdout"
runs = 5  # number of runs
modes = ["success", "error_code"]

# GPT-5.2 pricing table (USD per 1M tokens)
INPUT_COST_PER_1M = 1.75
OUTPUT_COST_PER_1M = 14.00

# ----------------

# parse file by explicit section headers: MODE: {success} RUN: {1}
header_re = re.compile(r"MODE:\s*\{([^}]+)\}\s*RUN:\s*\{(\d+)\}")
token_re = re.compile(r"(\d+)\s*/\s*(\d+)")

run_buckets = defaultdict(lambda: defaultdict(lambda: {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0,
}))

current_mode = None
current_run = None

with open(file_path) as f:
    for raw_line in f:
        line = raw_line.strip()

        header_match = header_re.search(line)
        if header_match:
            current_mode = header_match.group(1)
            current_run = int(header_match.group(2))
            continue

        token_match = token_re.search(line)
        if token_match and current_mode is not None and current_run is not None:
            output_tokens = int(token_match.group(1))
            total_tokens = int(token_match.group(2))
            input_tokens = total_tokens - output_tokens

            bucket = run_buckets[current_mode][current_run]
            bucket["input_tokens"] += input_tokens
            bucket["output_tokens"] += output_tokens
            bucket["total_tokens"] += total_tokens


def compute_cost(input_tokens, output_tokens):
    return (
        (input_tokens / 1_000_000) * INPUT_COST_PER_1M +
        (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
    )


for mode in modes:
    per_run = []

    for run in range(1, runs + 1):
        b = run_buckets[mode][run]
        run_cost = compute_cost(b["input_tokens"], b["output_tokens"])
        per_run.append({
            "run": run,
            "input_tokens": b["input_tokens"],
            "output_tokens": b["output_tokens"],
            "total_tokens": b["total_tokens"],
            "cost": run_cost,
        })

    mode_input = sum(r["input_tokens"] for r in per_run)
    mode_output = sum(r["output_tokens"] for r in per_run)
    mode_total = sum(r["total_tokens"] for r in per_run)
    mode_cost = sum(r["cost"] for r in per_run)

    avg_input = mode_input / runs
    avg_output = mode_output / runs
    avg_total = mode_total / runs
    avg_cost = mode_cost / runs

    print(f"=== {mode}: Mode Total ===")
    print({
        "mode": mode,
        "input_tokens": mode_input,
        "output_tokens": mode_output,
        "total_tokens": mode_total,
        "cost": mode_cost,
    })

    print(f"\n=== {mode}: Per Run ===")
    for r in per_run:
        print(r)

    print(f"\n=== {mode}: Run Average ===")
    print({
        "mode": mode,
        "avg_input_tokens": avg_input,
        "avg_output_tokens": avg_output,
        "avg_total_tokens": avg_total,
        "avg_cost": avg_cost,
    })
    print()