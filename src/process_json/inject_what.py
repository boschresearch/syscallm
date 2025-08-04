import os
import json
from utils import is_json
import argparse

def write_list_to_file(file_path, list_of_strings):
    with open(file_path, 'w') as file:
        for line in list_of_strings:
            file.write(f"{line}\n")


def json_to_strace(data, mode):
    """Convert JSON data to strace commands."""
    if not isinstance(data, dict) or 'name' not in data:
        return []

    syscall_name = data['name']
    strace_commands = []

    if mode == "success" and 'test_values' in data:
        strace_commands = [f"inject={syscall_name}:retval={val}" for val in data['test_values']]
    elif mode == "error_code" and 'error_codes' in data:
        strace_commands = [f"inject={syscall_name}:error={val}" for val in data['error_codes']]

    return strace_commands


def process_json_file(json_file_path, mode):
    """Process a single JSON file and convert it to strace commands."""
    with open(json_file_path, 'r') as json_file:
        # data from JSON file
        data = json.load(json_file)
        # convert JSON data to strace commands
        strace_commands = json_to_strace(data, mode)

        if not strace_commands:
            return

        # output directory path
        output_dir_path = json_file_path.replace("json", "strace").replace(".json", ".txt")
        os.makedirs(os.path.dirname(output_dir_path), exist_ok=True)

        # write strace commands to file
        write_list_to_file(output_dir_path, strace_commands)


def process_run_directory(run_dir_path, mode):
    """Process all JSON files in a run directory."""
    for filename in os.listdir(run_dir_path):
        json_file_path = os.path.join(run_dir_path, filename)
        if filename.endswith(".json") and is_json(json_file_path):
            process_json_file(json_file_path, mode)


def process_model_directory(model_dir_path, mode):
    """Process all run directories in a model directory."""
    for run in os.listdir(model_dir_path):
        print(run, end=" ")
        run_dir_path = os.path.join(model_dir_path, run)
        if os.path.isdir(run_dir_path):
            process_run_directory(run_dir_path, mode)
    print()


def process_all_models(json_dir_path, mode):
    """Process all model directories in the given JSON directory."""
    for model in os.listdir(json_dir_path):
        model_dir_path = os.path.join(json_dir_path, model)
        print(f"Converting {model_dir_path} to strace commands...", end=" ")
        if os.path.isdir(model_dir_path):
            process_model_directory(model_dir_path, mode)


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Process JSON files to strace commands.")
    parser.add_argument("--json-dir-path", type=str, help="Path to the directory containing JSON files (can be relative or absolute).")
    parser.add_argument("--mode", type=str, required=True, help="Fault injection mode (e.g., 'error_code', 'success')")
    args = parser.parse_args()

    # get json directory path
    json_dir_path = os.path.abspath(args.json_dir_path)
    json_dir_path = os.path.join(json_dir_path, args.mode)

    process_all_models(json_dir_path, args.mode)