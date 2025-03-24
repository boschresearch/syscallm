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


def parse_strace_file(file_path):
    """Parse the strace file and extract faults."""
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return [line.strip() for line in lines if line.strip()]


def process_run_directory(run_dir_path):
    """Process all strace files in a run directory."""
    for filename in os.listdir(run_dir_path):
        if filename.endswith(".strace"):
            strace_file_path = os.path.join(run_dir_path, filename)

            strace_params = parse_strace_file(strace_file_path)

            # 1 injection = 1 config file
            for i, strace_param in enumerate(strace_params):
                # syscall name
                syscall = strace_param.split(":")[0].split("=")[1]
                # id
                id = syscall + str(i)

                # generate JSON content for safety-fuzzing config
                json_content = generate_json_content(id, strace_param)

                # output file path
                output_dir = os.path.dirname(strace_file_path).replace("strace", "config")
                output_file_path = os.path.join(output_dir, f"{id}.json")

                os.makedirs(output_dir, exist_ok=True)

                # write JSON content to file
                with open(output_file_path, 'w') as json_file:
                    json.dump(json_content, json_file, indent=4)

                print(f"Generated JSON file: {output_file_path}")


def process_model_directory(model_dir_path):
    """Process all run directories in a model directory."""
    for run in os.listdir(model_dir_path):
        run_dir_path = os.path.join(model_dir_path, run)
        process_run_directory(run_dir_path)


def process_all_models(strace_dir):
    """Main function to process all model directories."""
    for model in os.listdir(strace_dir):
        model_dir_path = os.path.join(strace_dir, model)
        process_model_directory(model_dir_path)


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Process strace files to safety-fuzzing testbed config commands.")
    parser.add_argument("--strace-dir-path", type=str, help="Relative path to the directory containing files to generated strace fault injection parameter.")
    args = parser.parse_args()

    # get current directory path and json directory path
    cur_dir_path = os.getcwd()
    strace_dir_path = os.path.join(cur_dir_path, args.strace_dir_path)

    process_all_models(strace_dir_path)