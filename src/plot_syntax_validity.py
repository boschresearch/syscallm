import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import seaborn as sns
from utils import is_json, get_total_count
import config

plt.rcParams["font.family"] = "Times New Roman"

runs = config.runs
models = config.models

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

def categorize_batch(json_dirs):
    valid = []
    invalid = []
    invalid_stuck_in_loop = []
    invalid_format = []

    for json_dir in json_dirs:
        valid_json, invalid_json = categorize_valid_invalid(json_dir)
        stuck_in_loop_json, format_json = find_why_invalid(invalid_json, json_dir)

        valid.append(valid_json)
        invalid.append(invalid_json)
        invalid_stuck_in_loop.append(stuck_in_loop_json)
        invalid_format.append(format_json)
    
    return valid, invalid, invalid_stuck_in_loop, invalid_format

def find_why_invalid(invalid, json_dir):
    invalid_stuck_in_loop = []
    invalid_format = []

    model_name = os.path.basename(os.path.dirname(json_dir))
    if model_name.startswith("gpt-4"):
        stuck_in_loop = get_stuck_in_loop_by_error(invalid, json_dir)
    else:
        stuck_in_loop = get_stuck_in_loop(invalid, json_dir)

    for filename in invalid:
        if filename in stuck_in_loop:
            invalid_stuck_in_loop.append(filename)
        else:
            invalid_format.append(filename)

    return invalid_stuck_in_loop, invalid_format

def get_stuck_in_loop(invalid, json_dir):
    stuck_in_loop = []
    matches = {"}": "{", "]": "["}

    for filename in invalid:
        file_path = os.path.join(json_dir, filename + '.json')

        queue = []

        with open(file_path, 'r') as file:
            for line in file:
                for char in line:
                    if char in matches.values():
                        queue.append(char)
                    elif char in matches.keys():
                        if queue and queue[-1] == matches[char]:
                            queue.pop()
                        else:
                            stuck_in_loop.append(filename)
                            return stuck_in_loop

            if queue:
                stuck_in_loop.append(filename)

    return stuck_in_loop

def get_stuck_in_loop_by_error(invalid, json_dir):
    stuck_in_loop = []
    
    for filename in invalid:
        file_path = os.path.join(json_dir, filename + '.json')

        with open(file_path, 'r') as file:
            if file.read().startswith("LengthFinishReasonError"):
                stuck_in_loop.append(filename)

    return stuck_in_loop

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(__file__, "../../data"))

    total_count = get_total_count(base_dir)

    model_counts = {}

    df = pd.DataFrame(columns=['model_name', 'run', 'count'])

    for model in models:
        json_dirs = [os.path.join(base_dir, 'json', model, f'run{i}') for i in range(1, runs + 1)]

        valid, _, _, _ = categorize_batch(json_dirs)

        for run_index, valid_run in enumerate(valid, start=1):
            df = pd.concat([df, pd.DataFrame({'model_name': [model], 'run': [run_index], 'count': [len(valid_run)]})], ignore_index=True)

    plt.figure(figsize=(5, 4))
    
    plt.axhline(y=total_count, color='black', linestyle='--', label='Total')

    palette = sns.color_palette('rocket', len(df['model_name'].unique()))
    barplot = sns.barplot(
        data=df,
        x='model_name',
        y='count',
        capsize=0.2,
        err_kws={'linewidth': 1},
        palette=palette
    )

    # Add percentage labels
    for p in barplot.patches:
        height = p.get_height()
        percentage = f'{(height / total_count) * 100:.1f}%'
        barplot.text(
            p.get_x() + p.get_width() / 2., 
            height / 2,
            percentage, 
            ha="center", 
            va="center",
            fontsize=15,
            color="white"
        )

    model_names = df['model_name'].unique()
    bar_handles = [mpatches.Patch(color=palette[i], label=model_names[i]) for i in range(len(model_names))]
    line_handle = mlines.Line2D([], [], color='black', linestyle='--', label='Total')
    handles = [line_handle] + bar_handles

    plt.title("Syntax Validity", fontsize=16)
    plt.xlabel(None)
    plt.ylabel('Count', fontsize=15)
    plt.xticks([])
    plt.yticks(fontsize=12)
    plt.legend(handles=handles, fontsize=10, loc='upper left', bbox_to_anchor=(0, 0.95))
    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.show()
