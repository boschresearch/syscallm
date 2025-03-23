import os
import argparse
import json_to_strace
import strace_to_config

if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Process JSON files to strace commands.")
    parser.add_argument("--json_dir_path", type=str, help="Relative path to the directory containing JSON files.")
    parser.add_argument("--strace_dir_path", type=str, help="Relative path to the directory containing files to generated strace fault injection parameter.")
    parser.add_argument("--output_dir_path", type=str, help="Relative path to the directory to store the generated JSON files.")
    args = parser.parse_args()

    # get current directory path and json directory path
    cur_dir_path = os.getcwd()
    json_dir_path = os.path.join(cur_dir_path, args.json_dir_path)
    strace_dir_path = os.path.join(cur_dir_path, args.strace_dir_path)
    output_dir_path = os.path.join(cur_dir_path, args.output_dir_path)

    json_to_strace.process_all_models(json_dir_path)
    # TODO: filter out strace files that are not used in the application under test
    strace_to_config.process_all_models(strace_dir_path, output_dir_path)