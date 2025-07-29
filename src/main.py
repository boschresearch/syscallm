import os
import inject_what
import filter_strace
import inject_when
import strace_to_config
import random_config
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON files to generate the faultload.")
    parser.add_argument("--mode", type=str, required=True, help="Fault injection mode (e.g., 'error_code', 'success')")
    parser.add_argument("--distribution", type=str, required=True, help="Distribution type (e.g., 'uniform', 'log')")
    parser.add_argument("--aut", type=str, required=True, help="Application under test (e.g., 'redis', 'sha256')")
    args = parser.parse_args()

    mode = args.mode
    distribution = args.distribution
    aut = args.aut
    print(f"Running in {mode} mode with {distribution} distribution for {aut}")

    data_dir_path = os.path.abspath(os.path.join(os.getcwd(), "..", "data"))
    json_dir_path = os.path.join(data_dir_path, "json", mode)
    strace_dir_path = os.path.join(data_dir_path, "strace", mode)
    config_dir_path = os.path.join(data_dir_path, "config", mode)
    config_random_dir_path = os.path.join(data_dir_path, f"config_random_{distribution}", mode)

    # delete the directory if it already exists
    if os.path.exists(strace_dir_path):
        os.system(f"rm -r {strace_dir_path}")

    if os.path.exists(config_dir_path):
        os.system(f"rm -r {config_dir_path}")

    if os.path.exists(config_random_dir_path):
        os.system(f"rm -r {config_random_dir_path}")

    inject_what.process_all_models(json_dir_path, mode)
    filter_strace.process_all_models(strace_dir_path, aut)
    inject_when.process_all_models(strace_dir_path, aut)
    strace_to_config.process_all_models(strace_dir_path)
    random_config.process_all_models(config_dir_path, mode, distribution)