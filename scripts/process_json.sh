#!/bin/bash

# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKING_DIR="$(dirname "$SCRIPT_DIR")"

### assumption: the json file is already created on the GPU

# convert json files to strace command options
python3 ${WORKING_DIR}/src/process_json/main.py
