import os
import argparse
import app_syscalls


def get_when_params(target_syscall):
    # get the number of syscalls in the strace file for specific syscall
    count = app_syscalls.get_redis_syscalls()[target_syscall]
    
    # make when parameters
    return [f":when={i}..{i}" for i in range(1, count + 1)]


def process_strace_file(strace_file_path):
    # extract the file name without the extension
    strace_file_name = os.path.splitext(os.path.basename(strace_file_path))[0]

    when_params = get_when_params(strace_file_name)

    updated_lines = []

    with open(strace_file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            for when_param in when_params:
                updated_lines.append(line.strip() + when_param)

    with open(strace_file_path, "w") as f_out:
        f_out.write("\n".join(updated_lines))

    print(f"Added when parameters to {strace_file_path}.")


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
    parser = argparse.ArgumentParser(description="Filter out strace files that are not used in the application under test.")
    parser.add_argument("--strace-dir-path", type=str, help="Path to the directory containing files to generated strace fault injection parameters (can be relative or absolute).")
    args = parser.parse_args()

    # json directory path
    strace_dir_path = os.path.abspath(args.strace_dir_path)

    process_all_models(strace_dir_path)