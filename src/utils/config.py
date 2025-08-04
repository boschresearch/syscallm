runs = 5
models = ["Qwen2.5-7B-Instruct", "Qwen2.5-32B-Instruct", "QwQ-32B-Preview", "gpt-4o"]
temperature = ["0.3", "0.5", "0.7"]
mode = "success"
# mode = "error_code"
total_syscall_count = 345

# file paths
data_dir = "/home/jom8be/workspace/syscallm/data"

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