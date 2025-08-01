import os
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
    
    
def get_total_count(base_dir):
    """Get the total count of JSON files in a directory."""
    one_set = os.path.join(base_dir, 'json', models[0], 'run1')

    return len(os.listdir(one_set))