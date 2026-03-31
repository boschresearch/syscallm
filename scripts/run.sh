#!/bin/bash

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

# __author__      = "Min Hee Jo"
# __copyright__   = "Copyright 2026, Robert Bosch GmbH"
# __license__     = "AGPL"
# __version__     = "3.0"
# __email__       = "minhee.jo@de.bosch.com"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKING_DIR="$(dirname "$SCRIPT_DIR")"

# extract man pages for syscalls
bash "$WORKING_DIR/syscallm-generation/scripts/extract_syscall_man_pages.sh"

# check if nvidia-smi is available
if command -v nvidia-smi &> /dev/null; then
    # generate JSON files with LLMs
    bash "$WORKING_DIR/syscallm-generation/scripts/run.sh"
fi

# configure the environment variables
source "$WORKING_DIR/syscallm-injection/config/configure"

# process JSON files to strace command options
bash "$WORKING_DIR/scripts/process_json.sh"

# build the syscall monitor image
bash "$WORKING_DIR/syscallm-injection/scripts/build_monitor_image.sh"

# build the wrapped application image
bash "$WORKING_DIR/syscallm-injection/scripts/build_test_image.sh"

# overwrite environment variables for the testbed
export CONFIG_DIR="$TESTBED_PATH/examples/config"

# run error injection 
bash "$WORKING_DIR/syscallm-injection/scripts/run.sh"

# overwrite environment variables for the testbed
export CONFIG_DIR="$WORKING_DIR/data/config/success/gpt-4o/run1"

# run error injection 
bash "$WORKING_DIR/syscallm-injection/scripts/run.sh"

