# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

import os
import json
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config as config


models = config.models
runs = config.runs


def generate_json_content(id, fault):
    """Generate JSON content based on the faults."""
    return {
        "syslog_monitor_config": {
            "id": id,
            "strace_output": "/export/strace.output.{id}",
            "output": [
                {
                    "format": "csv",
                    "target": "/export/output.{id}.csv"
                }
            ],
            "faults": [fault]
        }
    }


def get_strace_params(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return [line.strip() for line in lines if line.strip()]


def process_strace_file(file_path):
    strace_params = get_strace_params(file_path)

    # 1 injection = 1 config file
    for i, strace_param in enumerate(strace_params):
        # syscall name
        syscall = strace_param.split(":")[0].split("=")[1]
        # id
        id = syscall + '_' + str(i + 1)

        # output file path
        output_file_path = os.path.dirname(file_path).replace("/strace/", "/config/")
        os.makedirs(output_file_path, exist_ok=True)
        output_file_path = os.path.join(output_file_path, f"{id}.json")

        # generate JSON content for syscallm-injection config
        json_content = generate_json_content(id, strace_param)

        # write JSON content to file
        with open(output_file_path, 'w') as json_file:
            json.dump(json_content, json_file, indent=4)


def process(directory, aut, mode):
    for model in models:
        for run in range(1, runs + 1):
            run_dir = os.path.join(directory, aut, mode, model, f"run{run}")

            for filename in os.listdir(run_dir):
                file_path = os.path.join(run_dir, filename)

                if file_path.endswith(".txt"):
                    process_strace_file(file_path)