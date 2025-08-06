import os
import json
import logging
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.utils as utils
import utils.config as config

logger = logging.getLogger(__name__)

mode = config.mode
temperature = config.temperature
models = config.models
runs = config.runs


def process_json_file(file_path):
    filename = os.path.splitext(os.path.basename(file_path))[0]

    with open(file_path, 'r') as file:
        data = json.load(file)

        syscall = data["name"]

        if filename != syscall:
            logger.warning(f"Filename {filename} does not match the system call {syscall}.")


def process(directory):
    for temp in (f"temperature_{t}" for t in temperature):
        for model in models:
            for run in range(1, runs + 1):
                run_dir = os.path.join(directory, temp, model, f"run{run}")

                for filename in os.listdir(run_dir):
                    file_path = os.path.join(run_dir, filename)

                    # only process valid JSON files
                    if utils.is_json(file_path):
                        process_json_file(file_path)