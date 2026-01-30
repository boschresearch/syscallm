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
    valid_empty, valid_out_of_bound = categorize_valid(valid, json_dir, mode)

    return valid, valid_empty, valid_out_of_bound, invalid

def categorize_valid_invalid(json_dir):
    valid = []
    invalid = []
    invalid_errors = []

    for filename in os.listdir(json_dir):
        file_path = os.path.join(json_dir, filename)

        if os.path.isfile(file_path) and file_path.endswith('.json'):
            man_page = filename.split('.json')[0]

            if utils.is_json(file_path):
                valid.append(man_page)
            else:
                invalid.append(man_page)
                with open(file_path, 'r') as f:
                    content = f.read()
                    invalid_errors.append(content)

    print(invalid_errors)
                
    return valid, invalid


def categorize_valid(valid, json_dir, mode):
    valid_empty = []
    valid_out_of_bound = []

    for filename in valid:
        filepath = os.path.join(json_dir, filename + '.json')

        with open(filepath, 'r') as f:
            content = json.load(f)

            if mode == "success":
                llm_generated_values = content["test_values"]
            elif mode == "error_code":
                llm_generated_values = content["error_codes"]
            
            if is_empty(llm_generated_values):
                valid_empty.append(filename)
            elif is_out_of_bound(llm_generated_values, mode):
                valid_out_of_bound.append(filename)

    return valid_empty, valid_out_of_bound


def find_duplicated(values):
    threshold = 3
    counts = Counter(values)
    return [item for item, count in counts.items() if count >= threshold]
    

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


if __name__ == "__main__":
    os.makedirs("figures", exist_ok=True)

    fig, axs = plt.subplots(nrows=2, figsize=(6, 3), sharex=True)

    for mode_idx, mode in enumerate(modes):
        df = pd.DataFrame(columns=[
            'mode', 'model_name', 'run',
            'total_valid_count', 'empty_count', 'out_of_bound_count', 'total_invalid_count',
        ])

        for model in models:
            for run in range(1, runs + 1):
                print(f"Processing mode={mode}, model={model}, run={run}...")
                json_dir = os.path.join(data_dir, "json", mode, model, f'run{run}')
                valid, valid_empty, valid_out_of_bound, invalid = categorize(json_dir, mode)
                df = pd.concat([df, pd.DataFrame({
                    'mode': [mode],
                    'model_name': [model],
                    'run': [run],
                    'total_valid_count': [len(valid)],
                    'empty_count': [len(valid_empty)],
                    'out_of_bound_count': [len(valid_out_of_bound)],
                    'total_invalid_count': [len(invalid)],
                })], ignore_index=True)

        # add percentage columns
        df['total_valid_percentage'] = (df['total_valid_count'] / total_syscall_count) * 100
        df['empty_percentage'] = (df['empty_count'] / total_syscall_count) * 100
        df['out_of_bound_percentage'] = (df['out_of_bound_count'] / total_syscall_count) * 100
        df['in_bound_percentage'] = df['total_valid_percentage'] - df['out_of_bound_percentage'] - df['empty_percentage']
        df['total_invalid_percentage'] = (df['total_invalid_count'] / total_syscall_count) * 100

        # pivot and merge valid/invalid for stacked bar
        df_valid_pivot = df.pivot_table(
            index=['mode', 'model_name'],
            values=['total_valid_percentage', 'in_bound_percentage', 'out_of_bound_percentage', 'empty_percentage'],
            aggfunc='mean'
        ).reset_index()
        df_invalid_pivot = df.pivot_table(
            index=['mode', 'model_name'],
            values=['total_invalid_percentage'],
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
        valid = df_combined_sorted['total_valid_percentage'].to_numpy()
        in_bound     = df_combined_sorted['in_bound_percentage'].to_numpy()
        out_of_bound = df_combined_sorted['out_of_bound_percentage'].to_numpy()
        invalid  = df_combined_sorted['total_invalid_percentage'].to_numpy()

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
        ax.barh(Y_POS, invalid, bar_h, label='Invalid', color='darkgrey', edgecolor='black', left=left)
        left += invalid

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
        Patch(facecolor='darkgrey', edgecolor='black', label='Invalid'),
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
