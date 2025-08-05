import os
import json
import random
import numpy as np
import re
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config as config

mode = config.mode
temperature = config.temperature
models = config.models
runs = config.runs
aut = config.aut

cache_value = {}
cache_count = {}

def get_count(syscall, invocation_num):
    global cache_count

    key = (syscall, invocation_num)

    if cache_count.get(key) is None:
        cache_count[key] = 0

    return cache_count[key]


def increment_count(syscall, invocation_num):
    global cache_count

    cache_count[(syscall, invocation_num)] = cache_count.get((syscall, invocation_num)) + 1


def get_current_value_count(syscall):
    global cache_value

    if syscall not in cache_value:
        return 0
    else:
        return len(cache_value[syscall])


def add_value(key, value):
    global cache_value

    if key not in cache_value:
        cache_value[key] = [value]
    else:
        cache_value[key].append(value)


def lookup_value(key, value):
    global cache_value

    if key not in cache_value:
        return False
    elif value not in cache_value[key]:
        return False
    else:
        return True


def draw_log_uniform_including_zero(max_value, p_zero=0.005):
    if np.random.rand() < p_zero:
        return np.uint64(0)
    else:
        log_min = np.log(1)
        log_max = np.log(np.uint64(max_value))
        log_sample = np.random.uniform(log_min, log_max)
        return np.uint64(np.exp(log_sample))


def get_random_number(mode, distribution):
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


def get_random_config(json_content, mode, distribution):
    """Generate a randomly generated fault injection config file."""
    global cache_value, cache_count

    # get id from json content
    id = json_content["syslog_monitor_config"]["id"]
    # extract system call name from id
    system_call = id[:id.rfind("_")]

    for fault in json_content["syslog_monitor_config"]["faults"]:
        # extract the invocation number from the fault
        invocation_num = re.search(r":when=(\d+)", fault).group(1)

        # get the count of the system call and invocation number that are processed
        cur_invocation_cnt = get_count(system_call, invocation_num)
        # get the current number of values in the cache for the system call
        cur_value_cnt = get_current_value_count(system_call)

        if cur_invocation_cnt < cur_value_cnt:
            # get a random number from the cache
            random_number = cache_value[system_call][cur_invocation_cnt]
        else:
            # generate a new random number
            random_number = get_random_number(mode, distribution)
            # check if the random number is already in the cache
            while lookup_value(system_call, random_number):
                # generate a new random number
                random_number = get_random_number(mode, distribution)
            # add the random number to the cache
            add_value(system_call, random_number)

        # increment the count for the system call and invocation number
        increment_count(system_call, invocation_num)

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
    output_path = file_path.replace("/config/", f"/config_random_{distribution}/")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # generate random JSON content
    random_json_content = get_random_config(json_content, mode, distribution)

    # write random JSON content to file
    with open(output_path, 'w') as file:
        json.dump(random_json_content, file, indent=4)
                

def process(directory, distribution):
    for temp in (f"temperature_{t}" for t in temperature):
        for model in models:
            for run in range(1, runs + 1):
                run_dir = os.path.join(directory, temp, model, f"run{run}")

                global cache_count, cache_value
                cache_value = {}
                cache_count = {}

                for filename in os.listdir(run_dir):
                    file_path = os.path.join(run_dir, filename)

                    process_json_file(file_path, distribution)