import os
import json
import argparse

def generate_json_content(id, fault):
    """Generate JSON content based on the faults."""
    return {
        "syslog_monitor_config": {
            "id": id,
            "strace_output": "/export/strace.output.{id}",
            "output": [
                {
                    "format": "csv",
                    "target": "/export/output.{id}.csv"
                }
            ],
            "faults": [fault]
        }
    }


def get_strace_params(file_path):
    """Parse the strace file and extract faults."""
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return [line.strip() for line in lines if line.strip()]


def process_strace_file(strace_file_path):
    strace_params = get_strace_params(strace_file_path)

    # 1 injection = 1 config file
    for i, strace_param in enumerate(strace_params):
        # syscall name
        syscall = strace_param.split(":")[0].split("=")[1]
        # id
        id = syscall + str(i)

        # output file path
        output_dir_path = os.path.dirname(strace_file_path).replace("strace", "config")
        output_file_path = os.path.join(output_dir_path, f"{id}.json")

        os.makedirs(output_dir_path, exist_ok=True)

        # generate JSON content for safety-fuzzing config
        json_content = generate_json_content(id, strace_param)

        # write JSON content to file
        with open(output_file_path, 'w') as json_file:
            json.dump(json_content, json_file, indent=4)

        print(f"Generated JSON file: {output_file_path}")


def process_run_directory(run_dir_path):
    """Process all strace files in a run directory."""
    for filename in os.listdir(run_dir_path):
        if filename.endswith(".strace"):
            strace_file_path = os.path.join(run_dir_path, filename)
            process_strace_file(strace_file_path)


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
    parser = argparse.ArgumentParser(description="Process strace files to safety-fuzzing testbed config commands.")
    parser.add_argument("--strace-dir-path", type=str, help="Path to the directory containing files to generated strace fault injection parameters (can be relative or absolute).")
    args = parser.parse_args()

    # json directory path
    strace_dir_path = os.path.abspath(args.strace_dir_path)

    process_all_models(strace_dir_path)