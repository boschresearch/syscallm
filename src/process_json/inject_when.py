# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

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


def get_when_params(syscall):
    # get the list of syscalls with its count
    syscalls = app_syscalls.syscall_getters[aut]()
    # get the total count for specific syscall
    count = syscalls.get(syscall, 0)

    # make when parameters
    return [f":when={i}..{i}" for i in range(1, count + 1)]


def process_strace_file(file_path):
    # extract the file name without the extension
    filename = os.path.splitext(os.path.basename(file_path))[0]

    when_params = get_when_params(filename)

    updated_lines = []

    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            for when_param in when_params:
                updated_lines.append(line.strip() + when_param)

    with open(file_path, "w") as f_out:
        f_out.write("\n".join(updated_lines))


def process(directory):
    for temp in (f"temperature_{t}" for t in temperature):
        for model in models:
            for run in range(1, runs + 1):
                run_dir = os.path.join(directory, temp, model, f"run{run}")

                for filename in os.listdir(run_dir):
                    file_path = os.path.join(run_dir, filename)

                    if file_path.endswith(".txt"):
                        process_strace_file(file_path)