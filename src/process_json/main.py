import os
import argparse
import inject_what
import filter_strace
import inject_when
import strace_to_config
import random_config
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config as config

mode = config.mode
data_dir = config.data_dir
json_dir = config.json_dir
json_filtered_dir = config.json_filtered_dir
strace_dir = config.strace_dir
config_dir = config.config_dir
config_random_uniform_dir = config.config_random_uniform_dir
config_random_log_dir = config.config_random_log_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON files to generate the errorload.")
    parser.add_argument("--aut", type=str, required=True, help="Application under test (e.g., 'redis', 'sha256')")
    args = parser.parse_args()

    aut = args.aut
    print(f"Running in {mode} mode for {aut}")

    # directories to remove if they exist
    dirs_to_remove = [
        json_filtered_dir,
        strace_dir,
        config_dir,
        config_random_uniform_dir,
        config_random_log_dir,
    ]

    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            os.system(f"rm -r {dir_path}")

    inject_what.process_all_models(json_dir_path, mode)
    filter_strace.process_all_models(strace_dir_path, aut)
    inject_when.process_all_models(strace_dir_path, aut)
    strace_to_config.process_all_models(strace_dir_path)
    random_config.process_all_models(config_dir_path, mode, "uniform")
    random_config.process_all_models(config_dir_path, mode, "log")