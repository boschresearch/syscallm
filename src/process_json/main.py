# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

import os
import logging
import filter_syscall
import filter_out_of_bound
import inject_what
import inject_when
import strace_to_config
import sample_config
import random_config
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config as config

logging.basicConfig(
    level=logging.INFO,  # Set default logging level
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

modes = config.modes
auts = config.auts
data_dir = config.data_dir
baseline = config.baseline
json_dir = data_dir / "json"
json_filtered_dir = data_dir / "json_filtered"
strace_dir = data_dir / "strace"
config_dir = data_dir / "config"
config_random_dir = data_dir / f"config_random_{baseline}"


if __name__ == "__main__":
    print(f" * Preprocess JSON files for {auts}? (y/n): ", end="")
    user_input = input().strip().lower()
    if user_input != "y":
        print("Exiting...")
        sys.exit(0)

    for aut in auts:
        for mode in modes:
            logging.info(f"=== Processing for AUT {aut} in {mode} mode ===")

            # directories to remove if they exist
            dirs_to_remove = [
                json_filtered_dir / mode,
                strace_dir / aut / mode, 
                config_dir / aut / mode,
                config_random_dir / aut / mode
            ]

            for dir_path in dirs_to_remove:
                if os.path.exists(dir_path):
                    os.system(f"rm -r {dir_path}")

            logging.info("1. Filtering System Calls...")
            filter_syscall.process(directory=json_dir, aut=aut, mode=mode)

            logging.info("2. Filtering out of bound values from filtered JSON files...")
            filter_out_of_bound.process(directory=json_filtered_dir, mode=mode)

            logging.info("3. Converting JSON files to strace commands...")
            inject_what.process(directory=json_filtered_dir, aut=aut, mode=mode)

            logging.info("4. Adding when parameter to the strace commands...")
            inject_when.process(directory=strace_dir, aut=aut, mode=mode)

            logging.info("5. Convert strace commands to error injection config files...")
            strace_to_config.process(directory=strace_dir, aut=aut, mode=mode)

            logging.info("6. Sampling...")
            sample_config.process(directory=config_dir, aut=aut, mode=mode)

            logging.info("7. Generating random config files...")
            random_config.process(directory=config_dir, aut=aut, mode=mode, distribution=baseline)

    # directories to remove if they exist
    dirs_to_remove = [
        json_filtered_dir,
        strace_dir, 
    ]

    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            os.system(f"rm -r {dir_path}")
