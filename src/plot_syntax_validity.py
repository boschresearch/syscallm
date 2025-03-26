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
            'Invalid': [len(invalid_run) for invalid_run in invalid],
            'Invalid Stuck in Loop': [len(invalid_stuck_in_loop_run) for invalid_stuck_in_loop_run in invalid_stuck_in_loop],
            'Invalid Format': [len(invalid_format_run) for invalid_format_run in invalid_format]
        }

        means = {key: np.mean([counts[key] for _ in range(runs)]) for key in counts}
        std_devs = {key: np.std([counts[key] for _ in range(runs)]) for key in counts}

        model_counts[model] = (means, std_devs)

    plt.figure(figsize=(12, 6))

    labels = list(model_counts[models[0]][0].keys())
    x = np.arange(len(labels))
    width = 0.2

    plt.axhline(y=total_count, color='black', linestyle='--', label='Total')

    for i, model in enumerate(models):
        means, std_devs = model_counts[model]
        values = [means[label] for label in labels]
        errors = [std_devs[label] for label in labels]

        plt.bar(x + i * width, values, width, yerr=errors, label=model, capsize=5)

    plt.xlabel('File Type')
    plt.ylabel('Count')
    plt.title(f"Average Syntax Correctness over {runs} runs for different models")
    plt.xticks(x + width / 2, [label for label in labels])
    plt.legend()

    plt.grid(True)

    for i, model in enumerate(models):
        means, std_devs = model_counts[model]
        for j, label in enumerate(labels):
            percentage = (means[label] / total_count) * 100
            print(f'{model} {label}: {percentage:.1f}% / std_dev: {std_devs[label]}')
            plt.text(x[j] + i * width, values[j] + errors[j], f'{percentage:.1f}%', ha='center', va='bottom')

    plt.show()
