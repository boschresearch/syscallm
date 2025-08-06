import os
import json
import random
import numpy as np
import re
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.app_syscalls as app_syscalls
import utils.config as config

mode = config.mode
temperature = config.temperature
models = config.models
runs = config.runs
aut = config.aut
syscalls = app_syscalls.syscall_getters[aut]()

cache_random_values = {}


def draw_log_uniform_including_zero(max_value, p_zero=0.005):
    if np.random.rand() < p_zero:
        return np.uint64(0)
    else:
        log_min = np.log(1)
        log_max = np.log(np.uint64(max_value))
        log_sample = np.random.uniform(log_min, log_max)
        return np.uint64(np.exp(log_sample))


def get_random_number(distribution):
    """Generate a random unsigned integer."""
    if mode == "success":
        if distribution == "uniform":
            return random.randint(0, 18446744073709551615)
        elif distribution == "log":
            return draw_log_uniform_including_zero(max_value=18446744073709551615)
    elif mode == "error_code":
        if distribution == "uniform":
            return random.randint(1, 4095)
        elif distribution == "log":
            return draw_log_uniform_including_zero(max_value=4095, p_zero=0)
        

def get_unique_random_numbers(distribution, count):
    unique_values = set()

    while len(unique_values) < count:
        val = get_random_number(distribution)
        unique_values.add(val)

    return list(unique_values)


def get_index(id_number, total_invocations):
    return (id_number - 1) % total_invocations


def get_random_config(json_content):
    global cache_random_values

    # get id from json content
    json_id = json_content["syslog_monitor_config"]["id"]
    # extract system call name and number from id
    id_syscall = json_id[:json_id.rfind("_")]
    id_number = int(json_id[json_id.rfind("_") + 1:])

    # total invocation count for the syscall
    total_invocations = syscalls[id_syscall]
    
    # cache index for the random number
    index = get_index(id_number, total_invocations)

    for fault in json_content["syslog_monitor_config"]["faults"]:
        random_number = cache_random_values.get(id_syscall)[index]

        if mode == "success":
            # replace the return value with the random number
            output_str = re.sub(r"retval=\d+", f"retval={str(random_number)}", fault)
        elif mode == "error_code":
            # replace the error code with the random number
            output_str = re.sub(r"error=[^:]+", f"error={str(random_number)}", fault)

        # update the json content with the random values
        json_content["syslog_monitor_config"]["faults"] = [output_str]

    return json_content


def process_json_file(file_path, distribution):
    with open(file_path, 'r') as file:
        json_content = json.load(file)

    # output file path
    output_file_path = file_path.replace("/config/", f"/config_random_{distribution}/")
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    print(file_path)
    # generate random JSON content
    random_json_content = get_random_config(json_content)

    # write random JSON content to file
    with open(output_file_path, 'w') as file:
        json.dump(random_json_content, file, indent=4)


def prefill_cache_random_values(distribution):
    global cache_random_values

    for syscall, count in syscalls.items():
        cache_random_values[syscall] = get_unique_random_numbers(distribution, count)


def extract_sort_keys(filename):
    # remove extension if present
    base = filename.rsplit('.', 1)[0]  
    
    # extract syscall name (before last '_') and number (after last '_')
    syscall, num = base.rsplit('_', 1)

    return (syscall, int(num))


def process(directory, distribution):
    global cache_random_values

    for temp in (f"temperature_{t}" for t in temperature):
        for model in models:
            for run in range(1, runs + 1):
                run_dir = os.path.join(directory, temp, model, f"run{run}")

                cache_random_values = {}
                prefill_cache_random_values(distribution)

                for filename in sorted(os.listdir(run_dir), key=extract_sort_keys):
                    file_path = os.path.join(run_dir, filename)

                    process_json_file(file_path, distribution)