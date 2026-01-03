# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

import os
import random
import logging
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config as config

logger = logging.getLogger(__name__)


models = config.models
runs = config.runs

sample_size = 1000
random.seed(42)

def collect_all_json_files(directory):
    return [
        os.path.join(directory, file)
        for file in os.listdir(directory)
        if file.endswith('.json')
    ]


def sample_files(directory):
    all_files = collect_all_json_files(directory)

    if len(all_files) > sample_size:
        return set(random.sample(all_files, sample_size)), set(all_files)
    return set(all_files), set(all_files)  # all files are selected


def process(directory, aut, mode):
    for model in models:
        for run in range(1, runs + 1):
            run_dir = os.path.join(directory, aut, mode, model, f"run{run}")

            selected, all_files = sample_files(run_dir)
            to_delete = all_files - selected

            for f in to_delete:
                os.remove(f)

            logger.debug(f"{len(selected)}/{len(all_files)} in {run_dir}")