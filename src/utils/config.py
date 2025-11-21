# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

import os

runs = 5
models = ["Qwen2.5-7B-Instruct", "Qwen2.5-32B-Instruct", "QwQ-32B-Preview", "gpt-4o"]
temperature = "0.5"
modes = ["success", "error_code"]
auts = ["python", "redis", "nginx"]
total_syscall_count = 345
baseline = "log"

# file paths
data_dir = "/home/jom8be/workspace/syscallm/data"