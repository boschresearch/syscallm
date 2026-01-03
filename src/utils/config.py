# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

from pathlib import Path

runs = 5
models = ["gpt-5"]
modes = ["success", "error_code"]
auts = ["python", "redis", "nginx"]
baseline = "log"
total_syscall_count = 345

# file paths
ROOT_DIR = Path(__file__).resolve().parents[2]
data_dir = ROOT_DIR / "data"
