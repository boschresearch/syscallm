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
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.app_syscalls as app_syscalls
import utils.config as config


models = config.models
runs = config.runs


def get_when_params(syscall, aut):
    # get the list of syscalls with its count
    syscalls = app_syscalls.syscall_getters[aut]()
    # get the total count for specific syscall
    count = syscalls.get(syscall, 0)

    # make when parameters
    return [f":when={i}..{i}" for i in range(1, count + 1)]


def process_strace_file(file_path, aut):
    # extract the file name without the extension
    filename = os.path.splitext(os.path.basename(file_path))[0]

    when_params = get_when_params(filename, aut)

    updated_lines = []

    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            for when_param in when_params:
                updated_lines.append(line.strip() + when_param)

    with open(file_path, "w") as f_out:
        f_out.write("\n".join(updated_lines))


def process(directory, aut, mode):
    for model in models:
        for run in range(1, runs + 1):
            run_dir = os.path.join(directory, aut, mode, model, f"run{run}")

            for filename in os.listdir(run_dir):
                file_path = os.path.join(run_dir, filename)

                if file_path.endswith(".txt"):
                    process_strace_file(file_path, aut)