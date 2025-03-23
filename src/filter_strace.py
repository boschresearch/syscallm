import os
import argparse

# TODO: better way of filtering syscalls
filter_only = ["access", "arch_prctl", "brk", "close", "dup", "execve", "exit_group", "fcntl", "futex", "getcwd", "getdents64", "getegid", "geteuid", "getgid", "getpid", "getrandom", "getuid", "ioctl", "lseek", "mmap", "mprotect", "munmap", "newfstatat", "openat", "pread64", "prlimit64", "read", "readlink", "rseq", "rt_sigaction", "set_robust_list", "set_tid_address", "sysinfo", "write"]

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
        if filename.endswith(".strace"):
            if os.path.splitext(filename)[0] not in filter_only:
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