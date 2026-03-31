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
import sys
import shutil
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.app_syscalls as app_syscalls
import utils.utils as utils
import utils.config as config


models = config.models
runs = config.runs


def move_file(file_path):
    output_file_path = file_path.replace("/json/", "/json_filtered/")
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    shutil.copy2(file_path, output_file_path)


def filter_syscall(file_path, aut):
    # list of syscalls with its count
    syscalls = app_syscalls.syscall_getters[aut]()
    base_filename = os.path.splitext(os.path.basename(file_path))[0]

    if syscalls is not None and base_filename in syscalls.keys():
        move_file(file_path)


def process(directory, aut, mode):
    for model in models:
        for run in range(1, runs + 1):
            run_dir = os.path.join(directory, mode, model, f"run{run}")

            for filename in os.listdir(run_dir):
                file_path = os.path.join(run_dir, filename)
                if utils.is_json(file_path):
                    filter_syscall(file_path, aut)