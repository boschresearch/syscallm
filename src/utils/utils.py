# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

import json
import utils.config as config

models = config.models

def is_json(file_path):
    """Check if a file is a valid JSON file."""
    try:
        with open(file_path, 'r') as file:
            json.load(file)
        return True
    except (ValueError, json.JSONDecodeError):
        return 