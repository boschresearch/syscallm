#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKING_DIR="$(dirname "$SCRIPT_DIR")"

### assumption: the json file is already created on the GPU

# covert json files to strace command options
python3 ${WORKING_DIR}/src/process_json/main.py --mode="success" --aut=$APPLICATION_NAME
python3 ${WORKING_DIR}/src/process_json/main.py --mode="error_code" --aut=$APPLICATION_NAME
