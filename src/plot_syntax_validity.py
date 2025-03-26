import os
import matplotlib.pyplot as plt
import numpy as np
from utils import is_json, get_total_count
import config

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
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stdout_dir = os.path.join(base_dir, 'stdout')

    total_count = get_total_count(base_dir)

    model_counts = {}

    for model in models:
        json_dirs = [os.path.join(base_dir, 'json', model, f'run{i}') for i in range(1, runs + 1)]

        valid, invalid, invalid_stuck_in_loop, invalid_format = categorize_batch(json_dirs)

        counts = {
            'Valid': [len(valid_run) for valid_run in valid],
            'Invalid': [len(invalid_run) for invalid_run in invalid]
        }

        model_counts[model] = counts

    plt.figure(figsize=(8, 6))

    labels = list(model_counts[models[0]].keys())
    # positions of the bars
    x = np.arange(len(labels))
    width = 0.15

    plt.axhline(y=total_count, color='black', linestyle='--', label='Total')

    for i, model in enumerate(models):
        counts = model_counts[model]
        values = [counts[label][0] for label in labels]

        # set greyscale color based on model index, ensuring no white color
        grey_value = 0.25 + (i / len(models)) * 0.6
        color = (grey_value, grey_value, grey_value)

        plt.bar(x + i * width, values, width, label=model, color=color)

    plt.xlabel('File Type', fontsize=15)
    plt.ylabel('Count', fontsize=15)
    plt.title(f"Syntax Correctness across Different Models", fontsize=16)
    plt.xticks(x + width, [label for label in labels], fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(fontsize=12)

    plt.grid(True)

    # add percentage labels above the bars
    for i, model in enumerate(models):
        counts = model_counts[model]
        for j, label in enumerate(labels):
            total_value = counts[label][0]
            percentage = (total_value / total_count) * 100

            # place text at the top of the bar
            plt.text(x[j] + i * width, total_value, f'{percentage:.1f}%', ha='center', va='bottom', fontsize=11)

    plt.show()
