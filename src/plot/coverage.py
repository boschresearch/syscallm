# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

import os
import re
import json
import errno
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import matplotlib.patheffects as path_effects
from collections import Counter
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.utils as utils
import utils.config as config

plt.rcParams["font.family"] = "Times New Roman"

runs = config.runs
total_syscall_count = config.total_syscall_count
modes = config.modes
models = config.models
data_dir = config.data_dir


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

if __name__ == "__main__":
    fig, axs = plt.subplots(nrows=2, figsize=(6, 3), sharex=True)
    hallucinatory_error_codes = {model: [] for model in models}

    for mode_idx, mode in enumerate(modes):
        df_valid = pd.DataFrame(columns=[
            'mode', 'model_name', 'run',
            'total_count', 'not_usable_count', 'out_of_bound_count'
        ])
        df_invalid = pd.DataFrame(columns=[
            'mode', 'model_name', 'run',
            'loop_count', 'enumeration_count', 'blocked_count'
        ])

        for model in models:
            for run in range(1, runs + 1):
                json_dir = os.path.join(data_dir, "json", mode, model, f'run{run}')
                valid, valid_empty, valid_all_out_of_bound, valid_out_of_bound, invalid, invalid_loop, invalid_enumeration, invalid_blocked = categorize(json_dir, mode)
                df_valid = pd.concat([df_valid, pd.DataFrame({
                    'mode': [mode],
                    'model_name': [model],
                    'run': [run],
                    'total_count': [len(valid)],
                    'not_usable_count': [len(valid_empty) + len(valid_all_out_of_bound)],
                    'out_of_bound_count': [len(valid_out_of_bound)]
                })], ignore_index=True)
                df_invalid = pd.concat([df_invalid, pd.DataFrame({
                    'mode': [mode],
                    'model_name': [model],
                    'run': [run],
                    'loop_count': [len(invalid_loop)],
                    'enumeration_count': [len(invalid_enumeration)],
                    'blocked_count': [len(invalid_blocked)]
                })], ignore_index=True)

        if mode == "error_code":
            print("Hallucinatory Error Codes:")
            for model, codes in hallucinatory_error_codes.items():
                sorted_codes = sorted(codes, key=lambda x: x[1], reverse=True)
                top_10 = sorted_codes[:10]
                print(f"Model: {model}, Top 10 Hallucinatory Error Codes:")
                for code, count in top_10:
                    print(f"  {code}: {count}")
                print()

        # add percentage columns
        df_valid['total_percentage'] = (df_valid['total_count'] / total_syscall_count) * 100
        df_valid['not_usable_percentage'] = (df_valid['not_usable_count'] / total_syscall_count) * 100
        df_valid['out_of_bound_percentage'] = (df_valid['out_of_bound_count'] / total_syscall_count) * 100
        df_valid['in_bound_percentage'] = df_valid['total_percentage'] - df_valid['out_of_bound_percentage'] - df_valid['not_usable_percentage']
        df_invalid['loop_percentage'] = (df_invalid['loop_count'] / total_syscall_count) * 100
        df_invalid['enumeration_percentage'] = (df_invalid['enumeration_count'] / total_syscall_count) * 100
        df_invalid['blocked_percentage'] = (df_invalid['blocked_count'] / total_syscall_count) * 100

        # pivot and merge valid/invalid for stacked bar
        df_valid_pivot = df_valid.pivot_table(
            index=['mode', 'model_name'],
            values=['in_bound_percentage', 'out_of_bound_percentage', 'not_usable_percentage'],
            aggfunc='mean'
        ).reset_index()
        df_invalid_pivot = df_invalid.pivot_table(
            index=['mode', 'model_name'],
            values=['loop_percentage', 'enumeration_percentage', 'blocked_percentage'],
            aggfunc='mean'
        ).reset_index().infer_objects(copy=False).fillna(0)

        # merge valid and invalid pivots
        df_combined = pd.merge(
            df_valid_pivot,
            df_invalid_pivot,
            on=['mode', 'model_name'],
            how='outer'
        ).reset_index().infer_objects(copy=False).fillna(0)

        # sort for plotting
        df_combined_sorted = df_combined.sort_values(['model_name'])
        # get all stacked segments
        in_bound     = df_combined_sorted['in_bound_percentage'].to_numpy()
        out_of_bound = df_combined_sorted['out_of_bound_percentage'].to_numpy()
        enumeration  = df_combined_sorted['enumeration_percentage'].to_numpy()
        loop         = df_combined_sorted['loop_percentage'].to_numpy()

        df_combined_sorted.to_csv(f"figures/coverage_{mode}.csv", index=False)

        # stacked horizontal bar plot
        ax = axs[mode_idx]
        Y_POS = np.arange(len(models))
        bar_h = 0.6
        left = np.zeros_like(in_bound)
        ax.barh(Y_POS, in_bound, bar_h, label='Clean', color='white', edgecolor='black', left=left)
        left += in_bound
        ax.barh(Y_POS, out_of_bound, bar_h, label='OOB', color='white', hatch='...', edgecolor='black', left=left)
        left += out_of_bound
        ax.barh(Y_POS, enumeration, bar_h, label='Enumeration', color='darkgrey', edgecolor='black', left=left)
        left += enumeration
        ax.barh(Y_POS, loop, bar_h, label='Looping', color='darkgrey', hatch='///', edgecolor='black', left=left)

        ax.set_yticks(Y_POS)
        ax.set_yticklabels(df_combined_sorted['model_name'], fontsize=9)
        ax.set_xlim(0, 100)
        ax.grid(axis='x', visible=True, linestyle='--', linewidth=0.5)
        ax.set_xticks(range(0, 101, 20))

        if mode == "success":
            ax.set_title("Nonnegative", fontsize=11)
        elif mode == "error_code":
            ax.set_title("Negative", fontsize=11)

    # dummy entries for group titles
    group_title_valid = Line2D([0], [0], color='none', label='Valid', linestyle='None')
    group_title_invalid = Line2D([0], [0], color='none', label='Invalid', linestyle='None')

    # actual legend handles
    valid_handles = [
        Patch(facecolor='white', edgecolor='black', label='Clean'),
        Patch(facecolor='white', edgecolor='black', hatch='...', label='OOB'),
    ]
    invalid_handles = [
        Patch(facecolor='darkgrey', edgecolor='black', label='Enumeration'),
        Patch(facecolor='darkgrey', edgecolor='black', hatch='///', label='Looping'),
    ]

    # combine all into one list with titles
    all_handles = [group_title_valid] + valid_handles + [group_title_invalid] + invalid_handles

    fig.legend(
        handles=all_handles,
        loc='center right',
        bbox_to_anchor=(1, 0.5),
        frameon=False,
        fontsize=9,
        ncol=1,
        handlelength=2,
        columnspacing=1
    )
    plt.subplots_adjust(hspace=0.2)
    fig.tight_layout(rect=[0, 0, 0.84, 1])
    fig.savefig("figures/coverage.png", dpi=300)
