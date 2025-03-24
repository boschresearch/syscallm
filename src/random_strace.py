import os
import argparse
import json
import random
import re

x_min = 0
x_max = 4294963200

def get_random_number():
    """Generate a random unsigned integer."""
    return random.randint(x_min, x_max)


def get_random_config(json_content):
    """Generate a randomly generated fault injection config file."""
    for fault in json_content["syslog_monitor_config"]["faults"]:
        # generate random number
        random_number = get_random_number()

        # replace the return value with the random number
        output_str = re.sub(r"retval=\d+", f"retval={str(random_number)}", fault)

    # update the json content with the random values
    json_content["syslog_monitor_config"]["faults"] = [output_str]

    return json_content


def process_json_file(json_file_path):
    with open(json_file_path, 'r') as file:
        json_content = json.load(file)

    # output file path
    output_file_path = json_file_path.replace("config", "config_random")
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    # generate random JSON content
    random_json_content = get_random_config(json_content)

    # write random JSON content to file
    with open(output_file_path, 'w') as file:
        json.dump(random_json_content, file, indent=4)

    print(f"Generated JSON file: {output_file_path}")


def process_run_directory(run_dir_path):
    """Process all json files in a run directory."""
    for filename in os.listdir(run_dir_path):
        if filename.endswith(".json"):
            json_file_path = os.path.join(run_dir_path, filename)
            process_json_file(json_file_path)
                

def process_model_directory(model_dir_path):
    """Process all run directories in a model directory."""
    for run in os.listdir(model_dir_path):
        run_dir_path = os.path.join(model_dir_path, run)
        if os.path.isdir(run_dir_path):
            process_run_directory(run_dir_path)


def process_all_models(strace_dir):
    """Main function to process all model directories."""
    for model in os.listdir(strace_dir):
        model_dir_path = os.path.join(strace_dir, model)
        if os.path.isdir(model_dir_path):
            process_model_directory(model_dir_path)


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Generate random strace fault injection parameters.")
    parser.add_argument("--config-dir-path", type=str, help="Path to the directory containing safety-fuzzing testbed config files (can be relative or absolute).")
    args = parser.parse_args()

    # get config directory path
    config_dir_path = os.path.abspath(args.config_dir_path)

    process_all_models(config_dir_path)