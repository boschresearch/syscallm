import os
import re
import json
import errno
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.utils as utils
import utils.config as config

plt.rcParams["font.family"] = "Times New Roman"

runs = config.runs
models = config.models
temperature = config.temperature
mode = config.mode
total_syscall_count = config.total_syscall_count
data_dir = config.data_dir


def categorize(json_dir):
    valid, invalid = categorize_valid_invalid(json_dir)
    valid_out_of_bound, valid_all_out_of_bound = find_valid_out_of_bound(valid, json_dir)
    invalid_stuck_in_loop, invalid_token_size_too_small = find_why_invalid(invalid, json_dir)

    return valid, valid_out_of_bound, valid_all_out_of_bound, invalid, invalid_stuck_in_loop, invalid_token_size_too_small


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


def find_why_invalid(invalid, json_dir):
    invalid_stuck_in_loop = []
    invalid_token_size_too_small = []

    model_name = os.path.basename(os.path.dirname(json_dir))

    for filename in invalid:
        filepath = os.path.join(json_dir, filename + '.json')

        with open(filepath, 'r') as f:
            content = f.read()

            if model_name.startswith("gpt-4"):
                if is_token_size_too_small_gpt(content):
                    invalid_token_size_too_small.append(filename)
                    continue

            llm_generated_values = extract_llm_generated_values(content)

            stuck = is_stuck_in_loop(llm_generated_values)

            if stuck:
                invalid_stuck_in_loop.append(filename)
            else:
                invalid_token_size_too_small.append(filename)

    return invalid_stuck_in_loop, invalid_token_size_too_small


def find_valid_out_of_bound(valid, json_dir):
    valid_out_of_bound = []
    valid_all_out_of_bound = []

    for filename in valid:
        filepath = os.path.join(json_dir, filename + '.json')

        with open(filepath, 'r') as f:
            content = json.load(f)

            if mode == "success":
                llm_generated_values = content["test_values"]
            elif mode == "error_code":
                llm_generated_values = content["error_codes"]
            
            out_of_bound = is_out_of_bound(llm_generated_values)
            all_out_of_bound = is_all_out_of_bound(llm_generated_values)
            
            if out_of_bound:
                valid_out_of_bound.append(filename)

            if all_out_of_bound:
                valid_all_out_of_bound.append(filename)

    return valid_out_of_bound, valid_all_out_of_bound


def extract_llm_generated_values(string: str):
    if mode == "success":
        return get_test_values(string)
    elif mode == "error_code":
        return get_error_codes(string)


def get_test_values(string: str):
    match = re.search(r'"test_values"\s*:\s*\[([^\]]*)\]?', string)

    if match:
        values_str = match.group(1)
        try:
            # match integers including negative values
            values = [int(v) for v in re.findall(r'-?\d+', values_str)]
        except ValueError as e:
            print(f"Error extracting test values: {e}")
            values = []
    else:
        print(f"No test values found")
        values = []
        
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


def is_stuck_in_loop(values: list):
    if find_duplicated(values):
        return True
    else:
        return False


def is_out_of_bound(values: list):
    if mode == "success":
        return any(v < 0 or v > 18446744073709551615 for v in values)
    elif mode == "error_code":
        return any(not hasattr(errno, v) for v in values)
    return False


def is_all_out_of_bound(values: list):
    if mode == "success":
        return all(v < 0 or v > 18446744073709551615 for v in values)
    elif mode == "error_code":
        return all(not hasattr(errno, v) for v in values)
    return False


def is_token_size_too_small_gpt(string: str):
    if string.startswith("LengthFinishReasonError"):
        return True
    return False


if __name__ == "__main__":
    # directories json data for each temperature
    temperature_dirs = [os.path.join(data_dir, "json", mode, f"temperature_{temp}") for temp in temperature]

    df_valid = pd.DataFrame(columns=['model_name', 'run', 'count', 'temperature'])
    df_invalid_all = pd.DataFrame(columns=['model_name', 'run', 'count', 'temperature', 'invalid_type'])

    for temp_dir, temp in zip(temperature_dirs, temperature):
        for model in models:
            for run in range(1, runs + 1):
                # directory to json data for each temperature, model, run
                json_dir = os.path.join(temp_dir, model, f'run{run}')

                # categorize valid and invalid json files
                valid, valid_out_of_bound, valid_all_out_of_bound, invalid, invalid_stuck_in_loop, invalid_token_size_too_small = categorize(json_dir)

                df_valid = pd.concat([df_valid, pd.DataFrame({'model_name': [model], 'run': [run], 'total_count': [len(valid)], 'out_of_bound_count': [len(valid_out_of_bound)], 'temperature': [temp]})], ignore_index=True)

                # add total count of invalid
                df_invalid = pd.DataFrame({
                    'model_name': [model] * 3,
                    'run': [run] * 3,
                    'count': [len(valid_out_of_bound), len(invalid_stuck_in_loop), len(invalid_token_size_too_small)],
                    'temperature': [temp] * 3,
                    'invalid_type': ['valid_out_of_bound', 'invalid_stuck_in_loop', 'invalid_token_size_too_small']
                })

                df_invalid_all = pd.concat([df_invalid_all, df_invalid], ignore_index=True)

                print(f"Model: {model}, Temperature: {temp}, Run: {run}, Number of Valid/Invalid: {len(valid)}/{len(invalid)},\nValid Out of Bound: {valid_out_of_bound}\nValid All Out of Bound: {valid_all_out_of_bound}\nInvalid Stuck in Loop: {invalid_stuck_in_loop},\nInvalid Token Size Too Small: {invalid_token_size_too_small}\n")

    # add percentage
    df_valid['total_percentage'] = (df_valid['total_count'] / total_syscall_count) * 100
    df_valid['out_of_bound_percentage'] = (df_valid['out_of_bound_count'] / total_syscall_count) * 100

    # prepare data for stacked bar plot
    df_valid['in_bound_percentage'] = df_valid['total_percentage'] - df_valid['out_of_bound_percentage']

    # set up the plot
    plt.figure(figsize=(10, 6))

    # pivot data for easier plotting
    df_plot = df_valid.pivot_table(
        index=['model_name', 'temperature'],
        values=['in_bound_percentage', 'out_of_bound_percentage'],
        aggfunc='mean'
    ).reset_index()

    # sort for consistent plotting
    df_plot = df_plot.sort_values(['model_name', 'temperature'])

    # get unique models and temperatures
    models_sorted = df_plot['model_name'].unique()
    temps_sorted = sorted(df_plot['temperature'].unique())

    # bar width and positions
    bar_width = 0.35
    n_temps = len(temps_sorted)
    x = []
    labels = []
    for i, model in enumerate(models_sorted):
        for j, temp in enumerate(temps_sorted):
            x.append(i * (n_temps + 1) + j)
            labels.append(f"{model}\n{temp}")

    # plot bars
    in_bound = df_plot['in_bound_percentage'].values
    out_bound = df_plot['out_of_bound_percentage'].values

    plt.bar(x, in_bound, bar_width, label='In Bound', color='skyblue')
    plt.bar(x, out_bound, bar_width, bottom=in_bound, label='Out of Bound', color='salmon')

    # x ticks and labels
    plt.xticks(x, labels, rotation=45, ha='right', fontsize=12)
    plt.xlabel('Model & Temperature', fontsize=16)
    plt.ylabel('Total Percentage (%)', fontsize=16)
    plt.ylim(0, 100)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.grid(axis='y', visible=True, linestyle='--', linewidth=0.5)

    plt.savefig(f"figures/coverage_{mode}.png", dpi=300)

    # figure size
    plt.figure(figsize=(6, 4))

    # calculate percentage for each invalid type
    df_invalid_all['percentage'] = (df_invalid_all['count'] / total_syscall_count) * 100

    # category plot for invalid causes including total invalid
    g = sns.catplot(
        data=df_invalid_all,
        x='temperature',
        y='percentage',
        hue='invalid_type',
        col='model_name',
        kind='bar',
        palette='mako',
        height=4,
        aspect=1
    )

    # plot parameters
    g.set_axis_labels('Temperature', 'Invalid Percentage (%)')
    g.set_titles('{col_name}')
    g.set(ylim=(0, 100))
    g.set_xticklabels(size=15)
    g.set_yticklabels(size=15)
    g._legend.set_title(None)
    g.tight_layout()

    for ax in g.axes.flatten():
        ax.grid(axis='y', visible=True, linestyle='--', linewidth=0.5)
        # Add percentage labels on top of each bar
        for bar in ax.containers:
            for rect in bar:
                height = rect.get_height()
                if height > 0:
                    ax.text(
                        rect.get_x() + rect.get_width() / 2,
                        height,
                        f'{height:.1f}%',
                        ha='center',
                        va='bottom',
                        fontsize=8
                    )

    plt.savefig(f"figures/coverage_invalid_causes_{mode}.png", dpi=300)
