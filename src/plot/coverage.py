import os
import re
import json
import errno
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.patheffects as path_effects
from collections import Counter
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.utils as utils
import utils.config as config

plt.rcParams["font.family"] = "Times New Roman"

runs = config.runs
total_syscall_count = config.total_syscall_count
data_dir = config.data_dir

models = ["Qwen2.5-7B-Instruct", "Qwen2.5-32B-Instruct", "QwQ-32B-Preview", "gpt-4o"]
temperature = ["0.3", "0.5", "0.7"]
modes = ["success", "error_code"]


def categorize(json_dir, mode):
    valid, invalid = categorize_valid_invalid(json_dir)
    valid_empty, valid_all_out_of_bound, valid_out_of_bound = categorize_valid(valid, json_dir, mode)
    invalid_loop, invalid_enumeration, invalid_blocked = categorize_invalid(invalid, json_dir)

    return valid, valid_empty, valid_all_out_of_bound, valid_out_of_bound, invalid, invalid_loop, invalid_enumeration, invalid_blocked


def categorize_valid_invalid(json_dir):
    valid = []
    invalid = []

    for filename in os.listdir(json_dir):
        file_path = os.path.join(json_dir, filename)

        if os.path.isfile(file_path) and file_path.endswith('.json'):
            man_page = filename.split('.json')[0]

            if utils.is_json(file_path):
                valid.append(man_page)
            else:
                invalid.append(man_page)
                
    return valid, invalid


def categorize_invalid(invalid, json_dir):
    invalid_loop = []
    invalid_enumeration = []
    invalid_blocked = []

    model_name = os.path.basename(os.path.dirname(json_dir))

    for filename in invalid:
        filepath = os.path.join(json_dir, filename + '.json')

        with open(filepath, 'r') as f:
            content = f.read()

            if model_name.startswith("gpt-4"):
                if is_enumeration_gpt(content):
                    invalid_enumeration.append(filename)
                    continue
                elif is_blocked_gpt(content):
                    invalid_blocked.append(filename)
                    continue

            llm_generated_values = extract_llm_generated_values(content, mode)

            loop = is_loop(llm_generated_values)

            if loop:
                invalid_loop.append(filename)
            else:
                invalid_enumeration.append(filename)

    return invalid_loop, invalid_enumeration, invalid_blocked


def categorize_valid(valid, json_dir, mode):
    valid_empty = []
    valid_out_of_bound = []
    valid_all_out_of_bound = []

    for filename in valid:
        filepath = os.path.join(json_dir, filename + '.json')
        model = os.path.basename(os.path.dirname(json_dir))

        with open(filepath, 'r') as f:
            content = json.load(f)

            if mode == "success":
                llm_generated_values = content["test_values"]
            elif mode == "error_code":
                llm_generated_values = content["error_codes"]
            
            if is_empty(llm_generated_values):
                valid_empty.append(filename)
            elif is_all_out_of_bound(llm_generated_values, mode):
                valid_all_out_of_bound.append(filename)
            elif is_out_of_bound(llm_generated_values, mode):
                valid_out_of_bound.append(filename)

            if mode == "error_code":
                update_hallucinatory_error_codes(model, llm_generated_values)

    return valid_empty, valid_all_out_of_bound, valid_out_of_bound


def extract_llm_generated_values(string: str, mode):
    if mode == "success":
        return get_test_values(string)
    elif mode == "error_code":
        return get_error_codes(string)


def get_test_values(string: str):
    values = []
    match = re.search(r'"test_values"\s*:\s*\[([^\]]*)\]?', string)

    if match:
        values_str = match.group(1)
        try:
            # match integers including negative values
            values = [int(v) for v in re.findall(r'-?\d+', values_str)]
        except ValueError as e:
            print(f"Error extracting test values: {e}")

    return values


def get_error_codes(string: str):
    match = re.search(r'"error_codes"\s*:\s*\[([^\]]*)', string)

    if not match:
        print("No error_codes found")
        codes = []

    values_str = match.group(1)

    codes = re.findall(r'"([A-Z0-9_]+)"', values_str)

    return codes


def find_duplicated(values):
    threshold = 3
    counts = Counter(values)
    return [item for item, count in counts.items() if count >= threshold]


def is_loop(values: list):
    if find_duplicated(values):
        return True
    else:
        return False
    

def is_empty(values:list):
    if not values:
        return True
    return False


def is_out_of_bound(values: list, mode):
    if mode == "success":
        return any(v < 0 or v > 18446744073709551615 for v in values)
    elif mode == "error_code":
        return any(not hasattr(errno, v) for v in values)
    return False


def is_all_out_of_bound(values: list, mode):
    if mode == "success":
        return all(v < 0 or v > 18446744073709551615 for v in values)
    elif mode == "error_code":
        return all(not hasattr(errno, v) for v in values)
    return False


def is_enumeration_gpt(string: str):
    if string.startswith("LengthFinishReasonError"):
        return True
    return False


def is_blocked_gpt(string: str):
    if string.startswith("ContentFilterFinishReasonError"):
        return True
    return False


def update_hallucinatory_error_codes(model, llm_generated_values):
    global hallucinatory_error_codes

    counters = dict(hallucinatory_error_codes[model])
    for v in llm_generated_values:
        if not hasattr(errno, v):
            counters[v] = counters.get(v, 0) + 1
    hallucinatory_error_codes[model] = list(counters.items())

def compute_x_positions(models, temperatures):
    n_temps = len(temperatures)
    x = []
    labels = []
    for i, _ in enumerate(models):
        for j, t in enumerate(temperatures):
            x.append(i * (n_temps + 1) + j)
            labels.append(t)
    return np.array(x), labels, n_temps


if __name__ == "__main__":
    fig_valid, axs_valid = plt.subplots(ncols=2, figsize=(11, 4), sharey=True)
    fig_invalid, axs_invalid = plt.subplots(ncols=2, figsize=(11, 4), sharey=True)
    
    X_POS, TEMP_LABELS, N_TEMPS = compute_x_positions(models, temperature)
    X_MIN, X_MAX = X_POS.min(), X_POS.max()
    
    hallucinatory_error_codes = {model: [] for model in models}

    for mode_idx, mode in enumerate(modes):
        df_valid = pd.DataFrame(columns=[
            'mode', 'model_name', 'run', 'temperature',
            'total_count', 'not_usable_count', 'out_of_bound_count'
        ])
        df_invalid = pd.DataFrame(columns=[
            'mode', 'model_name', 'run', 'temperature',
            'loop_count', 'enumeration_count', 'blocked_count'
        ])

        # directories json data for each temperature
        temperature_dirs = [
            os.path.join(data_dir, "json", mode, f"temperature_{temp}") for temp in temperature
        ]

        for temp_dir, temp in zip(temperature_dirs, temperature):
            for model in models:
                for run in range(1, runs + 1):
                    # directory to json data for each temperature, model, run
                    json_dir = os.path.join(temp_dir, model, f'run{run}')

                    # categorize valid and invalid json files
                    valid, valid_empty, valid_all_out_of_bound, valid_out_of_bound, invalid, invalid_loop, invalid_enumeration, invalid_blocked = categorize(json_dir, mode)

                    df_valid = pd.concat([df_valid, pd.DataFrame({
                        'mode': [mode],
                        'model_name': [model],
                        'run': [run],
                        'temperature': [temp],
                        'total_count': [len(valid)],
                        'not_usable_count': [len(valid_empty) + len(valid_all_out_of_bound)],
                        'out_of_bound_count': [len(valid_out_of_bound)]
                    })], ignore_index=True)

                    df_invalid = pd.concat([df_invalid, pd.DataFrame({
                        'mode': [mode],
                        'model_name': [model],
                        'run': [run],
                        'temperature': [temp],
                        'loop_count': [len(invalid_loop)],
                        'enumeration_count': [len(invalid_enumeration)],
                        'blocked_count': [len(invalid_blocked)]
                    })], ignore_index=True)

                    # print(f"Mode: {mode}, Model: {model}, Temperature: {temp}, Run: {run}, Number of Valid/Invalid: {len(valid)}/{len(invalid)},\nValid Empty: {valid_empty}\nValid Out of Bound: {valid_out_of_bound}\nValid All Out of Bound: {valid_all_out_of_bound}\nInvalid in Loop: {invalid_loop},\nInvalid Token Size Too Small: {invalid_enumeration}\n")

        if mode == "error_code":
            print("Hallucinatory Error Codes:")
            for model, codes in hallucinatory_error_codes.items():
                # sort codes by count descending
                sorted_codes = sorted(codes, key=lambda x: x[1], reverse=True)
                top_10 = sorted_codes[:10]
                print(f"Model: {model}, Top 10 Hallucinatory Error Codes:")
                for code, count in top_10:
                    print(f"  {code}: {count}")
                print()

        # add percentage
        df_valid['total_percentage'] = (df_valid['total_count'] / total_syscall_count) * 100
        df_valid['not_usable_percentage'] = (df_valid['not_usable_count'] / total_syscall_count) * 100
        df_valid['out_of_bound_percentage'] = (df_valid['out_of_bound_count'] / total_syscall_count) * 100
        df_valid['in_bound_percentage'] = df_valid['total_percentage'] - df_valid['out_of_bound_percentage'] - df_valid['not_usable_percentage']
        df_invalid['loop_percentage'] = (df_invalid['loop_count'] / total_syscall_count) * 100
        df_invalid['enumeration_percentage'] = (df_invalid['enumeration_count'] / total_syscall_count) * 100
        df_invalid['blocked_percentage'] = (df_invalid['blocked_count'] / total_syscall_count) * 100

        # pivot data for easier plotting, include empty_percentage and all_out_of_bound_percentage
        df_valid_pivot = df_valid.pivot_table(
            index=['mode', 'model_name', 'temperature'],
            values=['in_bound_percentage', 'out_of_bound_percentage', 'not_usable_percentage'],
            aggfunc='mean'
        ).reset_index()

        # pivot to get counts per invalid_type as columns
        df_invalid_pivot = df_invalid.pivot_table(
            index=['mode', 'model_name', 'temperature'],
            values=['loop_percentage', 'enumeration_percentage', 'blocked_percentage'],
            aggfunc='mean'
        ).reset_index()
        df_invalid_pivot = df_invalid_pivot.infer_objects(copy=False).fillna(0)

        valid_sorted = df_valid_pivot.sort_values(['model_name', 'temperature'])
        in_bound     = valid_sorted['in_bound_percentage'].to_numpy()
        out_of_bound = valid_sorted['out_of_bound_percentage'].to_numpy()
        not_usable   = valid_sorted['not_usable_percentage'].to_numpy()

        invalid_sorted = df_invalid_pivot.sort_values(['model_name', 'temperature'])
        enumeration  = invalid_sorted['enumeration_percentage'].to_numpy()
        loop         = invalid_sorted['loop_percentage'].to_numpy()
        blocked      = invalid_sorted['blocked_percentage'].to_numpy()

        print("Not Usable Percentages:", not_usable)
        print("Blocked Percentages:", blocked)
        
        # ---------------- VALID subplot ----------------
        ax_valid = axs_valid[mode_idx]
        bar_w_valid = 0.6

        ax_valid.bar(X_POS, in_bound, bar_w_valid, label='Clean', color='white', hatch='///', edgecolor='black')
        ax_valid.bar(X_POS, out_of_bound, bar_w_valid, bottom=in_bound, label='OOB', color='white', hatch='...', edgecolor='black')

        midpoints = [i * (N_TEMPS + 1) + (N_TEMPS - 1) / 2 for i in range(len(models))]
        
        ax_valid.set_xlim(X_MIN - 0.6, X_MAX + 0.6)
        ax_valid.set_xticks(X_POS)
        ax_valid.set_xticklabels(TEMP_LABELS, fontsize=10)
        for i, model in enumerate(models):
            ax_valid.text(midpoints[i], -10, model, ha='center', va='top', fontsize=10, transform=ax_valid.transData)

        ax_valid.set_ylim(0, 100)
        ax_valid.grid(axis='y', visible=True, linestyle='--', linewidth=0.5)
        ax_valid.set_yticks(range(0, 101, 10))
        ax_valid.set_title(f"{mode}", fontsize=13)

        # ---------------- INVALID subplot ----------------
        ax_invalid = axs_invalid[mode_idx]
        bar_w_inv = 0.6

        ax_invalid.bar(X_POS, enumeration, bar_w_inv, label='Enumeration', color='darkgrey', hatch='\\\\', edgecolor='black')
        ax_invalid.bar(X_POS, loop,        bar_w_inv, bottom=enumeration, label='Loop', color='darkgrey', hatch='oo', edgecolor='black')

        ax_invalid.set_xlim(X_MIN - 0.6, X_MAX + 0.6)
        ax_invalid.set_xticks(X_POS)
        ax_invalid.set_xticklabels(TEMP_LABELS, fontsize=10)
        for i, model in enumerate(models):
            ax_invalid.text(midpoints[i], -9, model, ha='center', va='top', fontsize=10, transform=ax_invalid.transData)

        ax_invalid.set_ylim(0, 100)
        ax_invalid.grid(axis='y', visible=True, linestyle='--', linewidth=0.5)
        ax_invalid.set_yticks(range(0, 101, 10))
        ax_invalid.set_title(f"{mode}", fontsize=13)

    valid_handles = [
        Patch(facecolor='white', edgecolor='black', hatch='///', label='Clean'),
        Patch(facecolor='white', edgecolor='black', hatch='...', label='OOB'),
    ]
    fig_valid.legend(
        handles=valid_handles,
        loc='upper left',
        ncol=1,
        frameon=True,
        bbox_to_anchor=(0.04, 0.92),
        fontsize=10
    )

    invalid_handles = [
        Patch(facecolor='darkgrey', edgecolor='black', hatch='\\\\', label='Enumeration'),
        Patch(facecolor='darkgrey', edgecolor='black', hatch='oo', label='Loop'),
    ]
    fig_invalid.legend(
        handles=invalid_handles,
        loc='upper left',
        ncol=1,
        frameon=True,
        bbox_to_anchor=(0.04, 0.92),
        fontsize=10
    )

    fig_valid.tight_layout()
    fig_valid.savefig("figures/coverage_valid.png", dpi=300)
    fig_invalid.tight_layout()
    fig_invalid.savefig("figures/coverage_invalid.png", dpi=300)
