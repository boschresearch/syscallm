import os

runs = 5
models = ["gpt-4o"]
temperature = ["0.3", "0.5", "0.7"]
mode = "success"
# mode = "error_code"
aut = os.environ.get("APPLICATION_NAME")
total_syscall_count = 345

# file paths
data_dir = "/home/jom8be/workspace/syscallm/data"
json_dir = os.path.join(data_dir, "json", mode)
json_filtered_dir = os.path.join(data_dir, "json_filtered", mode)
strace_dir = os.path.join(data_dir, "strace", aut, mode)
config_dir = os.path.join(data_dir, "config", aut, mode)
config_random_uniform_dir = os.path.join(data_dir, "config_random_uniform", aut, mode)
config_random_log_dir = os.path.join(data_dir, "config_random_log", aut, mode)

# TODO: data are missing
# file paths for each Ubuntu version
kernel_5_4_0 = "/home/jom8be/workspace/syscallm/data/syscall/syscalls_5.4.0.txt"
kernel_5_15_0 = "/home/jom8be/workspace/syscallm/data/syscall/syscalls_5.15.0.txt"
kernel_6_8_0 = "/home/jom8be/workspace/syscallm/data/syscall/syscalls_6.8.0.txt"
kernel_6_11_0 = "/home/jom8be/workspace/syscallm/data/syscall/syscalls_6.11.0.txt"

# file paths for missing syscalls
missing_5_15_0 = "/home/jom8be/workspace/syscallm/data/syscall/missing_syscalls_5.15.0.txt"
missing_6_8_0 = "/home/jom8be/workspace/syscallm/data/syscall/missing_syscalls_6.8.0.txt"
missing_6_11_0 = "/home/jom8be/workspace/syscallm/data/syscall/missing_syscalls_6.11.0.txt"