# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

import os
import random
import logging
import sys
import math
from typing import List, Tuple
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config as config

logger = logging.getLogger(__name__)


models = config.models
runs = config.runs
buffer = 10

random.seed(42)


def sample_size_95ci(N: int, error_margin: float = 0.03) -> int:
    """
    Compute sample size for a proportion with 95% CI and finite population correction.
    Worst-case p=0.5.
    """
    z = 1.96
    p = 0.5
    e = error_margin

    n0 = (z**2 * p * (1 - p)) / (e**2)
    n = n0 / (1 + (n0 - 1) / N)

    return math.ceil(n)


def get_sample_size(counts: List[int], error_margin: float = 0.03):
    N_min = min(counts)
    N_max = max(counts)

    n = sample_size_95ci(N_min, error_margin)
    # never sample more than available
    n = min(n, N_min)  

    # add buffer
    n_with_buffer = int(n * (1 + buffer))  
    # never sample more than available
    n_with_buffer = min(n_with_buffer, N_min)  

    return N_min, N_max, n_with_buffer, n


def collect_all_json_files(directory):
    return [
        os.path.join(directory, file)
        for file in os.listdir(directory)
        if file.endswith('.json')
    ]


def sample_files(directory, sample_size):
    all_files = collect_all_json_files(directory)

    return set(random.sample(all_files, sample_size)), set(all_files)


def process(directory, aut, mode):
    for model in models:
        counts = []

        for run in range(1, runs + 1):
            run_dir = os.path.join(directory, aut, mode, model, f"run{run}")

            # count the files in run_dir
            all_files = collect_all_json_files(run_dir)
            counts.append(len(all_files))

        N_min, N_max, n_with_buffer, n = get_sample_size(counts)
        logger.info(f"Model: {model} | Runs: {runs} | Min files: {N_min} | Max files: {N_max} | Sample size with {buffer * 100}% buffer: {n_with_buffer} | Sample size: {n}")

        # write original sample size to a file
        sample_size_file = os.path.join(directory, aut, mode, model, "sample_size.txt")
        with open(sample_size_file, "w") as f:
            f.write(f"{n}\n")

        for run in range(1, runs + 1):
            run_dir = os.path.join(directory, aut, mode, model, f"run{run}")

            # count the files in run_dir
            all_files = collect_all_json_files(run_dir)
            
            selected, all_files = sample_files(run_dir, n_with_buffer)
            to_delete = all_files - selected

            for f in to_delete:
                os.remove(f)

            logger.info(f"{len(selected)}/{len(all_files)} in {run_dir}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    base_directory = sys.argv[1]
    aut = sys.argv[2]
    mode = sys.argv[3]

    process(base_directory, aut, mode)
