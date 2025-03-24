import os
import argparse
import json_to_strace
import filter_strace
import strace_to_config
import random_strace

if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Process JSON files to strace commands.")
    parser.add_argument("--json-dir-path", type=str, help="Relative path to the directory containing JSON files.")
    args = parser.parse_args()

    # get current directory path and json directory path
    cur_dir_path = os.getcwd()
    json_dir_path = os.path.join(cur_dir_path, args.json_dir_path)
    strace_dir_path = os.path.join(cur_dir_path, "strace")
    config_dir_path = os.path.join(cur_dir_path, "config")

    # delete the directory if it already exists
    if os.path.exists(strace_dir_path):
        os.system(f"rm -r {strace_dir_path}")

    if os.path.exists(config_dir_path):
        os.system(f"rm -r {config_dir_path}")

    json_to_strace.process_all_models(json_dir_path)
    filter_strace.process_all_models(strace_dir_path)
    strace_to_config.process_all_models(strace_dir_path)
    random_strace.process_all_models(config_dir_path)