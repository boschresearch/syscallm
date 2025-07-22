import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import is_json
import config

plt.rcParams["font.family"] = "Times New Roman"

runs = config.runs
models = config.models
mode = config.mode

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

def categorize(json_dir):
    valid, invalid = categorize_valid_invalid(json_dir)
    stuck_in_loop, invalid_format = find_why_invalid(invalid, json_dir)

    return valid, invalid, stuck_in_loop, invalid_format


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
                valid, invalid, _, _ = categorize(json_dir)

                df = pd.concat([df, pd.DataFrame({'model_name': [model], 'run': [run], 'count': [len(valid)], 'temperature': [temp]})], ignore_index=True)

                if model == "gpt-4o":
                    print(f"Model: {model}, Temperature: {temp}, Run: {run}, Number of Valid/Invalid: {len(valid)}/{len(invalid)}, Invalid: {invalid}")

    # figure size
    plt.figure(figsize=(5, 4))
    
    # total number of syscalls
    total_count = 335

    # add percentage
    df['percentage'] = (df['count'] / total_count) * 100

    # calculate average percentage per model and temperature
    avg_percentage = df.groupby(['model_name', 'temperature'])['percentage'].mean()
    print("Average percentage per model and temperature:")
    print(avg_percentage.round(2))

    # calculate average count per model and temperature
    avg_count = df.groupby(['model_name', 'temperature'])['count'].mean()
    print("Average count per model and temperature:")
    print(avg_count.round(2))

    # color
    palette = sns.color_palette('rocket', len(df['model_name'].unique()))

    # line plot
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

    plt.show()
