import os
import argparse
import app_syscalls

def delete_file(file_path):
    """Delete a file."""
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    else:
        print(f"File does not exist: {file_path}")


def process_run_directory(run_dir_path):
    """Process all strace files in a run directory."""
    for filename in os.listdir(run_dir_path):
        file_path = os.path.join(run_dir_path, filename)
        if os.path.isfile(file_path) and filename.endswith(".strace"):
            base_filename = os.path.splitext(filename)[0]
            if base_filename not in app_syscalls.get_app_syscalls().keys():
                strace_file_path = os.path.join(run_dir_path, filename)
                delete_file(strace_file_path)


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
    parser = argparse.ArgumentParser(description="Filter out strace files that are not used in the application under test.")
    parser.add_argument("--strace-dir-path", type=str, help="Relative path to the directory containing files to generated strace fault injection parameter.")
    args = parser.parse_args()

    # get current directory path and strace directory path
    cur_dir_path = os.getcwd()
    strace_dir_path = os.path.join(cur_dir_path, args.strace_dir_path)

    # remove unwanted strace files
    process_all_models(strace_dir_path)