#!/usr/bin/env python

# Copyright (c) 2026 Robert Bosch GmbH and its subsidiaries.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__      = "Min Hee Jo"
__copyright__   = "Copyright 2026, Robert Bosch GmbH"
__license__     = "AGPL"
__version__     = "3.0"
__email__       = "minhee.jo@de.bosch.com"

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