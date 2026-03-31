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
import errno
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.utils as utils
import utils.config as config


models = config.models
runs = config.runs


def filter_out_of_bound_values(values, mode):
    if mode == "success":
        return [v for v in values if 0 <= v and v <= 18446744073709551615]
    elif mode == "error_code":
        return [v for v in values if hasattr(errno, v)]


def get_llm_generated_values(data, mode):
    if mode == "success":
        return data["test_values"]
    elif mode == "error_code":
        return data["error_codes"]
    

def set_llm_generated_values(data, values, mode):
    if mode == "success":
        data["test_values"] = values
    elif mode == "error_code":
        data["error_codes"] = values


def process_json_file(file_path, mode):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Failed to read {file_path}: {e}")
        return

    values = get_llm_generated_values(data, mode)
    filtered_values = filter_out_of_bound_values(values, mode)

    if not filtered_values:
        return

    set_llm_generated_values(data, filtered_values, mode)

    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
    except OSError as e:
        print(f"Failed to write {file_path}: {e}")


def process(directory, mode):
    for model in models:
        for run in range(1, runs + 1):
            run_dir = os.path.join(directory, mode, model, f"run{run}")

            for filename in os.listdir(run_dir):
                file_path = os.path.join(run_dir, filename)
                if utils.is_json(file_path):
                    process_json_file(file_path, mode)