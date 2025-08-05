import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.app_syscalls as app_syscalls
import utils.config as config

mode = config.mode
temperature = config.temperature
models = config.models
runs = config.runs
aut = config.aut

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        print(f"[ERROR] File does not exist: {file_path}")


def process_run_directory(file_path):
    if os.path.isfile(file_path) and file_path.endswith(".txt"):
        # list of syscalls with its count
        syscalls = app_syscalls.syscall_getters[aut]()
        base_filename = os.path.splitext(os.path.basename(file_path))[0]

        if syscalls is not None and base_filename not in syscalls.keys():
            delete_file(file_path)


def process(directory):
    for temp in (f"temperature_{t}" for t in temperature):
        for model in models:
            for run in range(1, runs + 1):
                run_dir = os.path.join(directory, temp, model, f"run{run}")

                for filename in os.listdir(run_dir):
                    file_path = os.path.join(run_dir, filename)
                    process_run_directory(file_path)
