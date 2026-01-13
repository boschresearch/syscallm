# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

from pathlib import Path


def extract_syscalls_from_statistics(aut: str):
    root_dir = Path(__file__).resolve().parents[2]
    file_path = f"{root_dir}/syscallm-injection/examples/statistics/{aut}.oracle"

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

    syscall_count = extract_syscalls_from_statistics(aut)
    syscall_count = sorted(syscall_count, key=lambda x: x[0])

    for syscall, count in syscall_count:
        print(f'"{syscall}": {count},')