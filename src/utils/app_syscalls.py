# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

import re
from pathlib import Path
from collections import defaultdict


ROOT_DIR = Path(__file__).resolve().parents[2]


def extract_syscalls_from_statistics(aut: str):
    file_path = f"{ROOT_DIR}/syscallm-injection/examples/statistics/{aut}.oracle"

    with open(file_path, 'r') as f:
        next(f)
        next(f)
        for line in f:
            parts = line.strip().split()
            syscall = parts[-1]
            count = parts[3]

            if '-' in syscall:
                break
            yield syscall, int(count)


def count_syscalls_from_strace(strace_file: str) -> dict:
    syscall_counts = defaultdict(int)
    pending_syscalls = {}  # Track unfinished syscalls: {(tid, syscall_name): count}
    
    try:
        with open(strace_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Extract TID from the beginning of the line
                tid_match = re.match(r'^(\d+)\s+', line)
                if not tid_match:
                    continue
                
                tid = int(tid_match.group(1))
                
                # Check if it's an unfinished syscall
                if '<unfinished ...>' in line:
                    syscall_match = re.search(r'(\w+)\s*\(', line)
                    if syscall_match:
                        syscall_name = syscall_match.group(1)
                        key = (tid, syscall_name)
                        pending_syscalls[key] = pending_syscalls.get(key, 0) + 1
                
                # Check if it's a resumed syscall
                elif '<... ' in line and 'resumed>' in line:
                    resumed_match = re.search(r'<\.\.\. (\w+) resumed>', line)
                    if resumed_match:
                        syscall_name = resumed_match.group(1)
                        key = (tid, syscall_name)
                        
                        # Match with pending unfinished syscall
                        if key in pending_syscalls and pending_syscalls[key] > 0:
                            pending_syscalls[key] -= 1
                        
                        # Count as a completed invocation
                        syscall_counts[syscall_name] += 1
                
                # Normal syscall (completed in one line)
                else:
                    syscall_match = re.search(r'(\w+)\s*\(', line)
                    if syscall_match:
                        syscall_name = syscall_match.group(1)
                        syscall_counts[syscall_name] += 1
        
        # Account for any unfinished syscalls that were never resumed
        for (tid, syscall_name), count in pending_syscalls.items():
            if count > 0:
                syscall_counts[syscall_name] += count
        
        return dict(syscall_counts)
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Strace output file not found: {strace_file}")
    except Exception as e:
        raise Exception(f"Error processing strace file: {e}")


# TODO: Update
def get_memcached_syscalls():
    return {
        "accept4": 1,
        "access": 14,
        "arch_prctl": 5,
        "bind": 4,
        "brk": 16,
        "chdir": 1,
        "clock_nanosleep": 189,
        "clone": 13,
        "clone3": 9,
        "close": 76,
        "connect": 14,
        "dup": 1,
        "dup2": 4,
        "epoll_create1": 5,
        "epoll_ctl": 11,
        "epoll_wait": 79,
        "eventfd2": 8,
        "execve": 5,
        "exit_group": 2,
        "fcntl": 10,
        "futex": 156,
        "getcwd": 1,
        "getegid": 29,
        "geteuid": 29,
        "getgid": 29,
        "getpeername": 1,
        "getpgrp": 1,
        "getpid": 8,
        "getppid": 3,
        "getrandom": 5,
        "getsockname": 6,
        "getsockopt": 1,
        "getuid": 30,
        "ioctl": 6,
        "listen": 2,
        "lseek": 11,
        "mkdir": 2,
        "mmap": 119,
        "mprotect": 41,
        "munmap": 12,
        "newfstatat": 128,
        "openat": 104,
        "pipe2": 5,
        "poll": 4,
        "pread64": 10,
        "prlimit64": 10,
        "pselect6": 1,
        "read": 56,
        "recvmsg": 6,
        "rseq": 14,
        "rt_sigaction": 52,
        "rt_sigprocmask": 66,
        "rt_sigreturn": 2,
        "sendmsg": 1,
        "sendto": 2,
        "set_robust_list": 18,
        "set_tid_address": 5,
        "setgid": 1,
        "setgroups": 1,
        "setsockopt": 9,
        "setuid": 1,
        "socket": 16,
        "statfs": 2,
        "sysinfo": 1,
        "umask": 2,
        "uname": 1,
        "wait4": 4,
        "write": 13
    }

def get_nginx_syscalls():
    return {
        "access": 9,
        "arch_prctl": 1,
        "brk": 3,
        "clone": 7,
        "close": 10,
        "connect": 2,
        "dup2": 1,
        "execve": 1,
        "fcntl": 3,
        "futex": 1,
        "getcwd": 1,
        "getegid": 9,
        "geteuid": 9,
        "getgid": 9,
        "getpgrp": 1,
        "getpid": 4,
        "getppid": 3,
        "getrandom": 1,
        "getuid": 9,
        "ioctl": 10,
        "lseek": 11,
        "mmap": 14,
        "mprotect": 4,
        "munmap": 1,
        "newfstatat": 45,
        "openat": 12,
        "pread64": 2,
        "prlimit64": 3,
        "read": 17,
        "rseq": 1,
        "rt_sigaction": 26,
        "rt_sigprocmask": 58,
        "rt_sigreturn": 6,
        "set_robust_list": 1,
        "set_tid_address": 1,
        "socket": 2,
        "sysinfo": 1,
        "uname": 1,
        "wait4": 13,
        "write": 2
    }

def get_python_syscalls():
    return {
        "access": 5,
        "arch_prctl": 1,
        "brk": 3,
        "clone": 2,
        "close": 10,
        "connect": 2,
        "dup2": 1,
        "execve": 1,
        "fcntl": 3,
        "futex": 1,
        "getcwd": 1,
        "getegid": 5,
        "geteuid": 5,
        "getgid": 5,
        "getpgrp": 1,
        "getpid": 4,
        "getppid": 3,
        "getrandom": 1,
        "getuid": 5,
        "ioctl": 6,
        "lseek": 5,
        "mmap": 14,
        "mprotect": 4,
        "munmap": 1,
        "newfstatat": 25,
        "openat": 12,
        "pread64": 2,
        "prlimit64": 3,
        "read": 11,
        "rseq": 1,
        "rt_sigaction": 18,
        "rt_sigprocmask": 19,
        "rt_sigreturn": 2,
        "set_robust_list": 1,
        "set_tid_address": 1,
        "socket": 2,
        "sysinfo": 1,
        "uname": 1,
        "wait4": 4,
        "write": 1
    }

def get_redis_syscalls():
    return {
        "access": 9,
        "arch_prctl": 1,
        "brk": 3,
        "clone": 13,
        "close": 12,
        "connect": 2,
        "dup2": 3,
        "execve": 1,
        "fcntl": 8,
        "futex": 1,
        "getcwd": 1,
        "getegid": 9,
        "geteuid": 9,
        "getgid": 9,
        "getpgrp": 1,
        "getpid": 4,
        "getppid": 3,
        "getrandom": 1,
        "getuid": 9,
        "ioctl": 23,
        "lseek": 23,
        "mmap": 15,
        "mprotect": 4,
        "munmap": 1,
        "newfstatat": 43,
        "openat": 13,
        "pread64": 2,
        "prlimit64": 3,
        "read": 23,
        "rseq": 1,
        "rt_sigaction": 40,
        "rt_sigprocmask": 136,
        "rt_sigreturn": 12,
        "set_robust_list": 1,
        "set_tid_address": 1,
        "socket": 2,
        "sysinfo": 1,
        "uname": 1,
        "wait4": 25,
        "write": 1
    }

syscall_getters = {
    "redis": get_redis_syscalls,
    "python": get_python_syscalls,
    "memcached": get_memcached_syscalls,
    "nginx": get_nginx_syscalls
}

if __name__ == "__main__":
    aut = input("Enter application name (redis/python/memcached/nginx): ")

    if aut == "nginx":
        syscall_count = count_syscalls_from_strace(f"{ROOT_DIR}/syscallm-injection/examples/statistics/{aut}.oracle")

        for syscall, count in syscall_count.items():
            print(f'"{syscall}": {count},')
    else:
        syscall_count = extract_syscalls_from_statistics(aut)
        syscall_count = sorted(syscall_count, key=lambda x: x[0])
        
        for syscall, count in syscall_count:
            print(f'"{syscall}": {count},')

    