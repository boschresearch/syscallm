import os
import argparse
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.app_syscalls as app_syscalls


def get_when_params(target_syscall, aut):
    # get the number of syscalls in the strace file for specific syscall
    if aut == "redis":
        count = app_syscalls.get_redis_syscalls()[target_syscall]
    elif aut == "sha256":
        count = app_syscalls.get_sha256_syscalls()[target_syscall]
    
    # make when parameters
    return [f":when={i}..{i}" for i in range(1, count + 1)]


def process_strace_file(strace_file_path, aut):
    # extract the file name without the extension
    strace_file_name = os.path.splitext(os.path.basename(strace_file_path))[0]

    when_params = get_when_params(strace_file_name, aut)

    updated_lines = []

    with open(strace_file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            for when_param in when_params:
                updated_lines.append(line.strip() + when_param)

    with open(strace_file_path, "w") as f_out:
        f_out.write("\n".join(updated_lines))


def process_run_directory(run_dir_path, aut):
    """Process all strace files in a run directory."""
    for filename in os.listdir(run_dir_path):
        if filename.endswith(".strace"):
            strace_file_path = os.path.join(run_dir_path, filename)
            process_strace_file(strace_file_path, aut)


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
        print(f"Creating when parameters for {model_dir_path}...", end=" ")
        if os.path.isdir(model_dir_path):
            process_model_directory(model_dir_path, aut)


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Filter out strace files that are not used in the application under test.")
    parser.add_argument("--strace-dir-path", type=str, help="Path to the directory containing files to generated strace fault injection parameters (can be relative or absolute).")
    parser.add_argument("--mode", type=str, required=True, help="Fault injection mode (e.g., 'error_code', 'success')")
    parser.add_argument("--aut", type=str, required=True, help="Application under test (e.g., 'redis', 'sha256')")
    args = parser.parse_args()

    # json directory path
    strace_dir_path = os.path.abspath(args.strace_dir_path)
    strace_dir_path = os.path.join(strace_dir_path, args.mode)

    process_all_models(strace_dir_path, args.aut)