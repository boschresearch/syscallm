import os
import inject_what
import filter_strace
import inject_when
import strace_to_config
import random_strace
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON files to generate the faultload.")
    parser.add_argument("--mode", type=str, required=True, help="Fault injection mode (e.g., 'error_code', 'success')")
    args = parser.parse_args()

    mode = args.mode
    print(f"Running in mode: {mode}")

    data_dir_path = os.path.join(os.getcwd(), "data")
    json_dir_path = os.path.join(data_dir_path, "json")
    strace_dir_path = os.path.join(data_dir_path, "strace")
    config_dir_path = os.path.join(data_dir_path, "config")

    # delete the directory if it already exists
    if os.path.exists(strace_dir_path):
        os.system(f"rm -r {strace_dir_path}")

    if os.path.exists(config_dir_path):
        os.system(f"rm -r {config_dir_path}")

    inject_what.process_all_models(json_dir_path, mode)
    filter_strace.process_all_models(strace_dir_path)
    inject_when.process_all_models(strace_dir_path)
    strace_to_config.process_all_models(strace_dir_path)
    
    random_runs = 5

    for i in range(random_runs):
        config_random_dir_path = os.path.join(data_dir_path, f"config_random_{i}")

        if os.path.exists(config_random_dir_path):
            os.system(f"rm -r {config_random_dir_path}")

        random_strace.process_all_models(config_dir_path, f"config_random_{i}", mode)

    os.system(f"rm -r {strace_dir_path}")