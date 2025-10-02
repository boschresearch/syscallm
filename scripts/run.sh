#!/bin/bash

# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

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

