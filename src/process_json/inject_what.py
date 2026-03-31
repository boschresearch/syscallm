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
import utils.utils as utils
import utils.config as config


models = config.models
runs = config.runs


def json_to_strace(data, syscall_name, mode):
    if not isinstance(data, dict):
        return []

    if mode == "success" and 'test_values' in data:
        return [f"inject={syscall_name}:retval={val}" for val in data['test_values']]
    elif mode == "error_code" and 'error_codes' in data:
        return [f"inject={syscall_name}:error={val}" for val in data['error_codes']]


def process_json_file(file_path, aut, mode):
    filename = os.path.splitext(os.path.basename(file_path))[0]

    with open(file_path, 'r') as file:
        try:    
            data = json.load(file)
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON from {file_path}: {e}")
            return
        
        # convert JSON data to strace commands
        strace_commands = json_to_strace(data, filename, mode)

        # if no strace commands are generated, skip writing the file
        if not strace_commands:
            return

        # output path
        output_file_path = file_path.replace("/json_filtered/", f"/strace/{aut}/").replace(".json", ".txt")
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    # write strace commands to file
    with open(output_file_path, 'w') as file:
        for line in strace_commands:
            file.write(f"{line}\n")


def process(directory, aut, mode):
    for model in models:
        for run in range(1, runs + 1):
            run_dir = os.path.join(directory, mode, model, f"run{run}")

            for filename in os.listdir(run_dir):
                file_path = os.path.join(run_dir, filename)

                # only process valid JSON files
                if utils.is_json(file_path):
                    process_json_file(file_path, aut, mode)