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
    syscall_name = data['name']
    test_values = data['test_values']

    return [f"inject={syscall_name}:retval={test_value}" for test_value in test_values]


def process_json_file(json_file_path):
    """Process a single JSON file and convert it to strace commands."""
    if is_json(json_file_path):
        with open(json_file_path, 'r') as json_file:
            print(f"Converting {json_file_path} to strace commands...")
            # data from JSON file
            data = json.load(json_file)
            # convert JSON data to strace commands
            strace_commands = json_to_strace(data)

            # output directory path
            output_dir_path = json_file_path.replace("json", "strace").replace(".json", ".txt")
            os.makedirs(os.path.dirname(output_dir_path), exist_ok=True)

            # write strace commands to file
            write_list_to_file(output_dir_path, strace_commands)


def process_run_directory(run_dir_path):
    """Process all JSON files in a run directory."""
    for filename in os.listdir(run_dir_path):
        if filename.endswith(".json"):
            json_file_path = os.path.join(run_dir_path, filename)
            process_json_file(json_file_path)


def process_model_directory(model_dir_path):
    """Process all run directories in a model directory."""
    for run in os.listdir(model_dir_path):
        run_dir_path = os.path.join(model_dir_path, run)
        process_run_directory(run_dir_path)


def main(json_dir_path):
    """Main function to process all model directories."""
    
    for model in os.listdir(json_dir_path):
        model_dir_path = os.path.join(json_dir_path, model)
        process_model_directory(model_dir_path)


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Process JSON files to strace commands.")
    parser.add_argument("json_dir_path", type=str, help="Relative path to the directory containing JSON files.")
    args = parser.parse_args()

    # get current directory path and json directory path
    cur_dir_path = os.getcwd()
    json_dir_path = os.path.join(cur_dir_path, args.json_dir_path)

    main(json_dir_path)