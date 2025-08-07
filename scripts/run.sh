#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKING_DIR="$(dirname "$SCRIPT_DIR")"

# extract man pages for syscalls
bash "$WORKING_DIR/llm-syscall/scripts/extract_syscall_man_pages.sh"

# check if nvidia-smi is available
if command -v nvidia-smi &> /dev/null; then
    # generate JSON files with LLMs
    bash "$WORKING_DIR/llm-syscall/scripts/run.sh"
fi

# configure the environment variables
source "$WORKING_DIR/safety-fuzzing/config/configure"

# process JSON files to strace command options
bash "$WORKING_DIR/scripts/process_json.sh"

# build the syscall monitor image
bash "$WORKING_DIR/safety-fuzzing/scripts/build_monitor_image.sh"

# build the wrapped application image
bash "$WORKING_DIR/safety-fuzzing/scripts/build_test_image.sh"

# overwrite environment variables for the testbed
export CONFIG_DIR="$TESTBED_PATH/examples/config"

# run error injection 
bash "$WORKING_DIR/safety-fuzzing/scripts/run.sh"

# overwrite environment variables for the testbed
export CONFIG_DIR="$WORKING_DIR/data/config/success/gpt-4o/run1"

# run error injection 
bash "$WORKING_DIR/safety-fuzzing/scripts/run.sh"

