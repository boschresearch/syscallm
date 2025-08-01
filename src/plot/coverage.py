import os
import re
import errno
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import is_json
import utils.config as config

plt.rcParams["font.family"] = "Times New Roman"

runs = config.runs
models = config.models
temperature = config.temperature
mode = config.mode


def categorize(json_dir):
    valid, invalid = categorize_valid_invalid(json_dir)
    invalid_stuck_in_loop, invalid_out_of_bound, invalid_token_size_too_small = find_why_invalid(invalid, json_dir)

    return valid, invalid, invalid_stuck_in_loop, invalid_out_of_bound, invalid_token_size_too_small


def categorize_valid_invalid(json_dir):
    valid = []
    invalid = []

    for filename in os.listdir(json_dir):
        file_path = os.path.join(json_dir, filename)

        if os.path.isfile(file_path) and file_path.endswith('.json'):
            man_page = filename.split('.json')[0]

            if is_json(file_path):
                valid.append(man_page)
            else:
                invalid.append(man_page)
                
    return valid, invalid


def find_why_invalid(invalid, json_dir):
    invalid_stuck_in_loop = []
    invalid_out_of_bound = []
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
            out_of_bound = is_out_of_bound(llm_generated_values)

            if stuck:
                invalid_stuck_in_loop.append(filename)
            
            if out_of_bound:
                invalid_out_of_bound.append(filename)

            if not stuck and not out_of_bound:
                invalid_token_size_too_small.append(filename)

    return invalid_stuck_in_loop, invalid_out_of_bound, invalid_token_size_too_small


def extract_llm_generated_values(string: str):
    if mode == "success":
        return get_test_values(string)
    elif mode == "error_code":
        return get_error_codes(string)


def get_test_values(string: str):
    match = re.search(r'"test_values"\s*:\s*\[([^\]]*)\]?', string)

    if match:
        # extract the test values substring
        values_str = match.group(1)

        try:
            values = [int(v.strip()) for v in values_str.split(',') if v.strip().isdigit()]
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


def is_token_size_too_small_gpt(string: str):
    if string.startswith("LengthFinishReasonError"):
        return True
    return False


if __name__ == "__main__":
    # directory to all json data
    data_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "json", mode))

    # directories json data for each temperature
    temperature = ["0.3", "0.5", "0.7"]
    temperature_dirs = [os.path.join(data_dir, f"temperature_{temp}") for temp in temperature]

    df = pd.DataFrame(columns=['model_name', 'run', 'count', 'temperature'])

    for temp_dir, temp in zip(temperature_dirs, temperature):
        for model in models:
            for run in range(1, runs + 1):
                # directory to json data for each temperature, model, run
                json_dir = os.path.join(temp_dir, model, f'run{run}')

                # categorize valid and invalid json files
                valid, invalid, invalid_stuck_in_loop, invalid_out_of_bound, invalid_token_size_too_small = categorize(json_dir)

                df = pd.concat([df, pd.DataFrame({'model_name': [model], 'run': [run], 'count': [len(valid)], 'temperature': [temp]})], ignore_index=True)

                # TODO: add total count of invalid
                df_invalid = pd.DataFrame({
                    'model_name': [model] * 3,
                    'run': [run] * 3,
                    'count': [len(invalid_stuck_in_loop), len(invalid_out_of_bound), len(invalid_token_size_too_small)],
                    'temperature': [temp] * 3,
                    'invalid_type': ['stuck_in_loop', 'out_of_bound', 'token_size_too_small']
                })

                if 'df_invalid_all' not in locals():
                    df_invalid_all = pd.DataFrame(columns=['model_name', 'run', 'count', 'temperature', 'invalid_type'])

                df_invalid_all = pd.concat([df_invalid_all, df_invalid], ignore_index=True)

                # print(f"Model: {model}, Temperature: {temp}, Run: {run}, Number of Valid/Invalid: {len(valid)}/{len(invalid)},\nInvalid Stuck in Loop: {invalid_stuck_in_loop},\nInvalid Out of Bound: {invalid_out_of_bound},\nInvalid Token Size Too Small: {invalid_token_size_too_small}\n")

    # total number of syscalls
    total_count = 345

    # figure size
    plt.figure(figsize=(5, 4))

    # add percentage
    df['percentage'] = (df['count'] / total_count) * 100

    # calculate average percentage per model and temperature
    avg_percentage = df.groupby(['model_name', 'temperature'])['percentage'].mean()
    avg_percentage = pd.to_numeric(avg_percentage, errors='coerce')
    print("Average percentage per model and temperature:")
    print(avg_percentage.round(2))

    # calculate average count per model and temperature
    avg_count = df.groupby(['model_name', 'temperature'])['count'].mean()
    avg_count = pd.to_numeric(avg_count, errors='coerce')
    print("Average count per model and temperature:")
    print(avg_count.round(2))

    # color
    palette = sns.color_palette('rocket', len(df['model_name'].unique()))

    # line plot for valid and invalid
    lineplot = sns.lineplot(
        data=df,
        x='temperature',
        y='percentage',
        hue='model_name',
        style='model_name',
        markers=True,
        markersize=12,
        palette=palette
    )

    # plot parameters
    plt.xlabel('Temperature', fontsize=16)
    plt.ylabel('Percentage (%)', fontsize=16)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.ylim(0, 100)
    plt.legend(fontsize=13, loc='upper right', bbox_to_anchor=(1, 0.45))
    plt.tight_layout()
    plt.grid(axis='y', visible=True, linestyle='--', linewidth=0.5)

    plt.savefig(f"figures/coverage_{mode}.png")

    # figure size
    plt.figure(figsize=(6, 4))

    # calculate percentage for each invalid type
    df_invalid_all['percentage'] = (df_invalid_all['count'] / total_count) * 100

    # category plot for invalid causes
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
    g.tight_layout()

    for ax in g.axes.flatten():
        ax.grid(axis='y', visible=True, linestyle='--', linewidth=0.5)

    plt.savefig(f"figures/coverage_invalid_causes_{mode}.png")
