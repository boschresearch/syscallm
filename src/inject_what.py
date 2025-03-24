import os
import json
from utils import is_json
import argparse

def write_list_to_file(file_path, list_of_strings):
    with open(file_path, 'w') as file:
        for line in list_of_strings:
            file.write(f"{line}\n")


def json_to_strace(data):
    """Convert JSON data to strace commands."""
    if 'name' not in data or 'test_values' not in data:
        return
    
    syscall_name = data['name']
    test_values = data['test_values']

    return [f"inject={syscall_name}:retval={test_value}" for test_value in test_values]


def process_json_file(json_file_path):
    """Process a single JSON file and convert it to strace commands."""
    with open(json_file_path, 'r') as json_file:
        print(f"Converting {json_file_path} to strace commands...")
        # data from JSON file
        data = json.load(json_file)
        # convert JSON data to strace commands
        strace_commands = json_to_strace(data)

        if not strace_commands:
            return

        # output directory path
        output_dir_path = json_file_path.replace("json", "strace").replace(".json", ".txt")
        os.makedirs(os.path.dirname(output_dir_path), exist_ok=True)

        # write strace commands to file
        write_list_to_file(output_dir_path, strace_commands)


def process_run_directory(run_dir_path):
    """Process all JSON files in a run directory."""
    for filename in os.listdir(run_dir_path):
        json_file_path = os.path.join(run_dir_path, filename)
        if filename.endswith(".json") and is_json(json_file_path):
            process_json_file(json_file_path)


def process_model_directory(model_dir_path):
    """Process all run directories in a model directory."""
    for run in os.listdir(model_dir_path):
        run_dir_path = os.path.join(model_dir_path, run)
        if os.path.isdir(run_dir_path):
            process_run_directory(run_dir_path)


def process_all_models(json_dir_path):
    """Process all model directories in the given JSON directory."""
    for model in os.listdir(json_dir_path):
        model_dir_path = os.path.join(json_dir_path, model)
        if os.path.isdir(model_dir_path):
            process_model_directory(model_dir_path)


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Process JSON files to strace commands.")
    parser.add_argument("--json-dir-path", type=str, help="Path to the directory containing JSON files (can be relative or absolute).")
    args = parser.parse_args()

    # get json directory path
    json_dir_path = os.path.abspath(args.json_dir_path)

    process_all_models(json_dir_path)