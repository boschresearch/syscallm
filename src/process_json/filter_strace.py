import os
import argparse
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.app_syscalls as app_syscalls

def delete_file(file_path):
    """Delete a file."""
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        print(f"[ERROR] File does not exist: {file_path}")


def process_run_directory(run_dir_path, aut):
    """Process all strace files in a run directory."""
    for filename in os.listdir(run_dir_path):
        file_path = os.path.join(run_dir_path, filename)
        if os.path.isfile(file_path) and filename.endswith(".strace"):
            base_filename = os.path.splitext(filename)[0]

            # check if the base filename is not in the app syscalls based on the application under test
            if aut == "redis":
                if base_filename not in app_syscalls.get_redis_syscalls().keys():
                    strace_file_path = os.path.join(run_dir_path, filename)
                    delete_file(strace_file_path)
            elif aut == "sha256":
                if base_filename not in app_syscalls.get_sha256_syscalls().keys():
                    strace_file_path = os.path.join(run_dir_path, filename)
                    delete_file(strace_file_path)


def process_model_directory(model_dir_path, aut):
    """Process all run directories in a model directory."""
    for run in os.listdir(model_dir_path):
        print(run, end=" ")
        run_dir_path = os.path.join(model_dir_path, run)
        if os.path.isdir(run_dir_path):
            process_run_directory(run_dir_path, aut)
    print()


def process_all_models(strace_dir, aut):
    """Main function to process all model directories."""
    for model in os.listdir(strace_dir):
        model_dir_path = os.path.join(strace_dir, model)
        print(f"Filtering {model_dir_path}...", end=" ")
        if os.path.isdir(model_dir_path):
            process_model_directory(model_dir_path, aut)


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Filter out strace files that are not used in the application under test.")
    parser.add_argument("--strace-dir-path", type=str, help="Path to the directory containing files to generated strace fault injection parameters (can be relative or absolute).")
    parser.add_argument("--mode", type=str, required=True, help="Fault injection mode (e.g., 'error_code', 'success')")
    parser.add_argument("--aut", type=str, required=True, help="Application under test (e.g., 'redis', 'sha256')")
    args = parser.parse_args()

    # get strace directory path
    strace_dir_path = os.path.abspath(args.strace_dir_path)
    strace_dir_path = os.path.join(strace_dir_path, args.mode)

    # remove unwanted strace files
    process_all_models(strace_dir_path, args.aut)