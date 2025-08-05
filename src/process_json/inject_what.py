import os
import json
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.utils as utils
import utils.config as config

mode = config.mode
temperature = config.temperature
models = config.models
runs = config.runs


def json_to_strace(data):
    if not isinstance(data, dict) or 'name' not in data:
        return []

    syscall_name = data['name']

    if mode == "success" and 'test_values' in data:
        return [f"inject={syscall_name}:retval={val}" for val in data['test_values']]
    elif mode == "error_code" and 'error_codes' in data:
        return [f"inject={syscall_name}:error={val}" for val in data['error_codes']]


def process_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        # convert JSON data to strace commands
        strace_commands = json_to_strace(data)

        # if no strace commands are generated, skip writing the file
        if not strace_commands:
            return

        # output path
        output_path = file_path.replace("/json_filtered/", "/strace/").replace(".json", ".txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # write strace commands to file
    with open(output_path, 'w') as file:
        for line in strace_commands:
            file.write(f"{line}\n")


def process(directory):
    for temp in [f"temperature_{temp}" for temp in temperature]:
        for model in models:
            for run in range(1, runs + 1):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, temp, model, f"run{run}", filename)

                    # only process valid JSON files
                    if utils.is_json(file_path):
                        process_json_file(file_path)