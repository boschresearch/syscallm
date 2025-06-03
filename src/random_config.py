import os
import argparse
import json
import random
import numpy as np
import re

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


def get_random_number(mode):
    """Generate a random unsigned integer."""
    if mode == "success":
        return draw_log_uniform_including_zero(max_value=18446744073709551615)
    elif mode == "error_code":
        # TODO: Update according to the new distribution
        return random.randint(1, 4095)


def get_random_config(json_content, mode):
    """Generate a randomly generated fault injection config file."""
    global cache

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
            random_number = cache_value[system_call][cur_invocation_cnt - 1]
        else:
            # generate a new random number
            random_number = get_random_number(mode)
            # check if the random number is already in the cache
            while lookup_value(system_call, random_number):
                # generate a new random number
                random_number = get_random_number(mode)
            # add the random number to the cache
            add_value(system_call, random_number)

        # increment the count for the system call and invocation number
        increment_count(system_call, invocation_num)

        # replace the return value with the random number
        output_str = re.sub(r"retval=\d+", f"retval={str(random_number)}", fault)

    # update the json content with the random values
    json_content["syslog_monitor_config"]["faults"] = [output_str]

    return json_content


def process_json_file(json_file_path, mode):
    with open(json_file_path, 'r') as file:
        json_content = json.load(file)

    # output file path
    output_file_path = json_file_path.replace("config", f"config_random_log")
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    # generate random JSON content
    random_json_content = get_random_config(json_content, mode)

    # write random JSON content to file
    with open(output_file_path, 'w') as file:
        json.dump(random_json_content, file, indent=4)

    print(f"Generated JSON file: {output_file_path}")


def process_run_directory(run_dir_path, mode):
    """Process all json files in a run directory."""
    for filename in os.listdir(run_dir_path):
        if filename.endswith(".json"):
            json_file_path = os.path.join(run_dir_path, filename)
            process_json_file(json_file_path, mode)
                

def process_model_directory(model_dir_path, mode):
    """Process all run directories in a model directory."""
    for run in os.listdir(model_dir_path):
        run_dir_path = os.path.join(model_dir_path, run)
        if os.path.isdir(run_dir_path):
            # reset the cache_count for each run directory
            global cache_count, cache_value
            cache_value = {}
            cache_count = {}

            process_run_directory(run_dir_path, mode)


def process_all_models(strace_dir, mode):
    """Main function to process all model directories."""
    for model in os.listdir(strace_dir):
        model_dir_path = os.path.join(strace_dir, model)
        if os.path.isdir(model_dir_path):
            process_model_directory(model_dir_path, mode)


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Generate random strace fault injection parameters.")
    parser.add_argument("--config-dir-path", type=str, help="Path to the directory containing safety-fuzzing testbed config files (can be relative or absolute).")
    parser.add_argument("--mode", type=str, required=True, help="Fault injection mode (e.g., 'error_code', 'success')")
    args = parser.parse_args()

    mode = args.mode
    print(f"Running in mode: {mode}")

    # get config directory path
    config_dir_path = os.path.abspath(args.config_dir_path)

    process_all_models(config_dir_path, mode)