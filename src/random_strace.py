import os
import argparse
import json
import random
import re

def set_id(json_content, str):
    json_content["syslog_monitor_config"]["id"] = str

    return json_content


def get_random_number(mode):
    """Generate a random unsigned integer."""
    if mode == "success":
        return random.randint(0, 4294963200)
    elif mode == "error_code":
        return random.randint(1, 4095)


def get_random_config(json_content, mode):
    """Generate a randomly generated fault injection config file."""
    for fault in json_content["syslog_monitor_config"]["faults"]:
        # generate random number
        random_number = get_random_number(mode)

        # replace the return value with the random number
        output_str = re.sub(r"retval=\d+", f"retval={str(random_number)}", fault)

    # update the json content with the random values
    json_content["syslog_monitor_config"]["faults"] = [output_str]

    return json_content


def process_json_file(json_file_path, mode, factor):
    with open(json_file_path, 'r') as file:
        json_content = json.load(file)

    # output file path
    output_file_path = json_file_path.replace("config", f"config_random")
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    # generate random JSON content
    random_json_content = get_random_config(json_content, mode)

    # write random JSON content to file
    with open(output_file_path, 'w') as file:
        json.dump(random_json_content, file, indent=4)

    for i in range(2, factor + 1):
        # output file path
        base, ext = os.path.splitext(output_file_path)
        new_output_file_path = base + f"-{i}" + ext

        # change id
        id = os.path.os.path.splitext(os.path.basename(new_output_file_path))[0]
        id_json_content = set_id(json_content, id)

        # generate random JSON content
        random_json_content = get_random_config(id_json_content, mode)

        # write random JSON content to file
        with open(new_output_file_path, 'w') as file:
            json.dump(random_json_content, file, indent=4)

    print(f"Generated JSON file: {output_file_path}")


def process_run_directory(run_dir_path, mode, factor):
    """Process all json files in a run directory."""
    for filename in os.listdir(run_dir_path):
        if filename.endswith(".json"):
            json_file_path = os.path.join(run_dir_path, filename)
            process_json_file(json_file_path, mode, factor)
                

def process_model_directory(model_dir_path, mode, factor):
    """Process all run directories in a model directory."""
    for run in os.listdir(model_dir_path):
        run_dir_path = os.path.join(model_dir_path, run)
        if os.path.isdir(run_dir_path):
            process_run_directory(run_dir_path, mode, factor)


def process_all_models(strace_dir, mode, factor):
    """Main function to process all model directories."""
    for model in os.listdir(strace_dir):
        model_dir_path = os.path.join(strace_dir, model)
        if os.path.isdir(model_dir_path):
            process_model_directory(model_dir_path, mode, factor)


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Generate random strace fault injection parameters.")
    parser.add_argument("--config-dir-path", type=str, help="Path to the directory containing safety-fuzzing testbed config files (can be relative or absolute).")
    parser.add_argument("--mode", type=str, required=True, help="Fault injection mode (e.g., 'error_code', 'success')")
    parser.add_argument("--factor", type=int, default=1, help="Factor to generate random test cases (default: 1).")
    args = parser.parse_args()

    mode = args.mode
    print(f"Running in mode: {mode}")

    # get config directory path
    config_dir_path = os.path.abspath(args.config_dir_path)

    process_all_models(config_dir_path, mode, args.factor)