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


if __name__ == "__main__":
    hallucinatory_error_codes = {model: [] for model in models}
    fig_valid, axs_valid = plt.subplots(nrows=2, figsize=(6, 8), sharex=True)
    fig_invalid, axs_invalid = plt.subplots(nrows=2, figsize=(6, 8), sharex=True)

    for mode in modes:
        df_valid = pd.DataFrame(columns=['mode', 'model_name', 'run', 'temperature', 'total_count', 'not_usable_count', 'out_of_bound_count'])
        df_invalid = pd.DataFrame(columns=['mode', 'model_name', 'run', 'temperature', 'loop_count', 'enumeration_count'])

        # directories json data for each temperature
        temperature_dirs = [os.path.join(data_dir, "json", mode, f"temperature_{temp}") for temp in temperature]

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
        
        ################################################# PLOT VALID COVERAGE #################################################

        # set up the plot for valid coverage (one subplot per mode)
        ax_valid = axs_valid[modes.index(mode)]
        bar_width = 0.6
        n_temps = len(temperature)
        x = []
        temp_labels = []
        for i, model in enumerate(models):
            for j, temp in enumerate(temperature):
                x.append(i * (n_temps + 1) + j)
                temp_labels.append(temp)

        not_usable = df_valid_pivot['not_usable_percentage'].values
        out_of_bound = df_valid_pivot['out_of_bound_percentage'].values
        in_bound = df_valid_pivot['in_bound_percentage'].values

        ax_valid.bar(x, in_bound, bar_width, label='In-Bounds', color='skyblue')
        ax_valid.bar(x, out_of_bound, bar_width, bottom=in_bound, label='OOB-Fixable', color='gold')
        ax_valid.bar(x, not_usable, bar_width, bottom=np.add(in_bound, out_of_bound), label='Not Usable', color='salmon')

        for i, val in enumerate(not_usable):
            if val > 0:
                bar_top = in_bound[i] + out_of_bound[i] + val
                ax_valid.text(
                    x[i],
                    bar_top + 0.5,
                    f'{val:.1f}%\nNot Usable',
                    ha='center',
                    va='bottom',
                    fontsize=10
                )

        ax_valid.set_xticks(x)
        ax_valid.set_xticklabels(temp_labels, fontsize=11)
        ax_valid.set_ylabel('Percentage (%)', fontsize=13)
        ax_valid.set_ylim(0, 110)
        ax_valid.grid(axis='y', visible=True, linestyle='--', linewidth=0.5)
        ax_valid.set_yticks(range(0, 101, 10))
        group_width = n_temps + 1
        midpoints = [i * group_width + (n_temps - 1) / 2 for i in range(len(models))]
        for i, model in enumerate(models):
            ax_valid.text(
            midpoints[i],
            -7,
            model,
            ha='center',
            va='top',
            fontsize=10,
            transform=ax_valid.transData
            )
        ax_valid.set_title(f"Valid Coverage - {mode}", fontsize=14)

        ################################################# PLOT INVALID CAUSES #################################################

        # set up the plot for invalid causes (one subplot per mode)
        ax_invalid = axs_invalid[modes.index(mode)]
        bar_width = 0.4
        n_temps = len(temperature)
        x = []
        temp_labels = []
        for i, model in enumerate(models):
            for j, temp in enumerate(temperature):
                x.append(i * (n_temps + 1) + j)
                temp_labels.append(temp)

        loop = np.array(df_invalid_pivot['loop_percentage'].values)
        enumeration = np.array(df_invalid_pivot['enumeration_percentage'].values)
        blocked = np.array(df_invalid_pivot['blocked_percentage'].values)

        ax_invalid.bar(x, enumeration, bar_width, label='Enumeration', color='mediumseagreen')
        ax_invalid.bar(x, loop, bar_width, bottom=enumeration, label='Loop', color='crimson')
        ax_invalid.bar(x, blocked, bar_width, bottom=enumeration + loop, label='Blocked', color='#9400D3')

        for i, (val_enum, val_loop, val_block) in enumerate(zip(enumeration, loop, blocked)):
            if val_enum > 0.0 and val_enum < 5.0:
                bar_top = val_enum
                ax_invalid.text(
                    x[i],
                    bar_top + 0.5,
                    f'{val_enum:.2f}%',
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    color='mediumseagreen',
                    path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=0.7, foreground='black')]
                )
            if val_loop > 0.0 and val_loop < 5.0:
                bar_top = val_enum + val_loop
                ax_invalid.text(
                    x[i],
                    bar_top + 0.5,
                    f'{val_loop:.2f}%',
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    color='crimson',
                    path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=0.7, foreground='black')]
                )
            if val_block > 0.0 and val_block < 5.0:
                bar_top = float(val_enum) + float(val_loop) + float(val_block)
                ax_invalid.text(
                    x[i],
                    bar_top + 0.5,
                    f'{val_block:.2f}%',
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    color='darkviolet',
                    path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=0.7, foreground='black')]
                )

        ax_invalid.set_xticks(x)
        ax_invalid.set_xticklabels(temp_labels, fontsize=10)
        ax_invalid.set_ylabel('Percentage (%)', fontsize=13)
        ax_invalid.set_ylim(0, 100)
        ax_invalid.grid(axis='y', visible=True, linestyle='--', linewidth=0.5)
        ax_invalid.set_yticks(range(0, 100, 10))
        group_width = n_temps + 1
        midpoints = [i * group_width + (n_temps - 1) / 2 for i in range(len(models))]
        for i, model in enumerate(models):
            ax_invalid.text(
            midpoints[i],
            -7,
            model,
            ha='center',
            va='top',
            fontsize=10,
            transform=ax_invalid.transData
            )
        ax_invalid.set_title(f"Invalid Causes - {mode}", fontsize=14)

    valid_handles = [
        Patch(color='skyblue', label='In-Bounds'),
        Patch(color='gold',    label='OOB-Fixable'),
        Patch(color='salmon',  label='Not Usable'),
    ]
    fig_valid.legend(
        handles=valid_handles,
        loc='upper left',
        ncol=1,
        frameon=True,
        bbox_to_anchor=(0.11, 0.955),
        fontsize=10
    )

    invalid_handles = [
        Patch(color='mediumseagreen', label='Enumeration'),
        Patch(color='crimson',        label='Loop'),
        Patch(color='#9400D3',        label='Blocked'),
    ]
    fig_invalid.legend(
        handles=invalid_handles,
        loc='upper left',
        ncol=1,
        frameon=True,
        bbox_to_anchor=(0.11, 0.955),
        fontsize=10
    )

    fig_valid.tight_layout(rect=[0, 0.08, 1, 1])
    fig_valid.savefig("figures/coverage_valid.png", dpi=300)
    fig_invalid.tight_layout(rect=[0, 0.08, 1, 1])
    fig_invalid.savefig("figures/coverage_invalid.png", dpi=300)
