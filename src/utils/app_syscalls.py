#!/usr/bin/env python

# Copyright (c) 2026 Robert Bosch GmbH and its subsidiaries.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__      = "Min Hee Jo"
__copyright__   = "Copyright 2026, Robert Bosch GmbH"
__license__     = "AGPL"
__version__     = "3.0"
__email__       = "minhee.jo@de.bosch.com"

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
        "read": 171,
        "getpid": 34,
        "write": 29,
        "execve": 8,
        "brk": 49,
        "mmap": 319,
        "access": 22,
        "openat": 178,
        "newfstatat": 225,
        "close": 349,
        "pread64": 20,
        "arch_prctl": 8,
        "set_tid_address": 8,
        "set_robust_list": 32,
        "rseq": 8,
        "mprotect": 75,
        "prlimit64": 12,
        "munmap": 11,
        "ioctl": 80,
        "getrandom": 10,
        "futex": 41,
        "getuid": 11,
        "getgid": 11,
        "geteuid": 32,
        "getegid": 11,
        "rt_sigprocmask": 82,
        "sysinfo": 3,
        "rt_sigaction": 113,
        "uname": 3,
        "getcwd": 1,
        "getppid": 4,
        "socket": 10,
        "connect": 9,
        "lseek": 34,
        "getpgrp": 1,
        "fcntl": 62,
        "dup2": 6,
        "clone": 24,
        "statfs": 8,
        "fadvise64": 3,
        "copy_file_range": 3,
        "exit_group": 8,
        "wait4": 13,
        "rt_sigreturn": 6,
        "epoll_create": 17,
        "getdents64": 2,
        "mkdir": 7,
        "chown": 5,
        "setsockopt": 6,
        "bind": 1,
        "listen": 2,
        "gettid": 22,
        "setsid": 1,
        "umask": 3,
        "pwrite64": 1,
        "socketpair": 33,
        "setgid": 16,
        "sendmsg": 120,
        "setgroups": 16,
        "setuid": 16,
        "prctl": 16,
        "eventfd2": 32,
        "epoll_ctl": 83,
        "io_setup": 16,
        "epoll_wait": 153,
        "recvmsg": 238,
        "clock_nanosleep": 1,
        "chdir": 1,
        "poll": 6,
        "accept4": 1,
        "getsockopt": 1,
        "getsockname": 3,
        "getpeername": 2,
        "sendto": 1,
        "recvfrom": 3,
        "writev": 1,
        "sendfile": 1,
        "rt_sigsuspend": 1
    }

def get_python_syscalls():
    return {
        "access": 9,
        "arch_prctl": 4,
        "brk": 27,
        "chdir": 1,
        "clone": 2,
        "close": 106,
        "close_range": 2,
        "connect": 2,
        "dup2": 4,
        "epoll_create1": 1,
        "execve": 9,
        "fadvise64": 1,
        "fcntl": 10,
        "futex": 17,
        "getcwd": 2,
        "getdents64": 24,
        "getegid": 5,
        "geteuid": 5,
        "getgid": 5,
        "getpgrp": 1,
        "getpid": 6,
        "getppid": 3,
        "getrandom": 6,
        "gettid": 2,
        "getuid": 5,
        "ioctl": 52,
        "lseek": 92,
        "mkdir": 2,
        "mmap": 105,
        "mprotect": 25,
        "munmap": 8,
        "newfstatat": 455,
        "open": 1,
        "openat": 116,
        "pipe2": 2,
        "pread64": 8,
        "prlimit64": 6,
        "read": 122,
        "readlink": 9,
        "rseq": 4,
        "rt_sigaction": 159,
        "rt_sigprocmask": 24,
        "rt_sigreturn": 2,
        "set_robust_list": 6,
        "set_tid_address": 4,
        "socket": 2,
        "statfs": 2,
        "sysinfo": 1,
        "umask": 2,
        "uname": 1,
        "vfork": 1,
        "wait4": 5,
        "write": 4
    }

def get_redis_syscalls():
    return {
        "accept4": 16,
        "access": 25,
        "arch_prctl": 14,
        "bind": 2,
        "brk": 45,
        "chdir": 1,
        "clock_nanosleep": 1,
        "clone": 18,
        "clone3": 5,
        "close": 153,
        "connect": 22,
        "dup2": 14,
        "epoll_create": 1,
        "epoll_ctl": 19,
        "epoll_wait": 40,
        "execve": 14,
        "fadvise64": 1,
        "fcntl": 54,
        "fdatasync": 1,
        "fsync": 1,
        "futex": 19,
        "getcwd": 2,
        "getegid": 11,
        "geteuid": 11,
        "getgid": 11,
        "getpeername": 1,
        "getpgrp": 1,
        "getpid": 54,
        "getppid": 3,
        "getrandom": 16,
        "getsockopt": 2,
        "getuid": 11,
        "ioctl": 58,
        "listen": 2,
        "lseek": 25,
        "madvise": 20,
        "mkdir": 2,
        "mmap": 352,
        "mprotect": 83,
        "munmap": 66,
        "newfstatat": 138,
        "open": 20,
        "openat": 112,
        "pipe2": 3,
        "poll": 10,
        "prctl": 5,
        "pread64": 28,
        "prlimit64": 17,
        "read": 142,
        "readlink": 10,
        "recvfrom": 22,
        "rename": 1,
        "rseq": 19,
        "rt_sigaction": 134,
        "rt_sigprocmask": 172,
        "rt_sigreturn": 12,
        "sched_getaffinity": 10,
        "sendto": 22,
        "set_robust_list": 32,
        "set_tid_address": 14,
        "setitimer": 1,
        "setsockopt": 83,
        "socket": 14,
        "statfs": 2,
        "sysinfo": 2,
        "umask": 4,
        "uname": 1,
        "unlinkat": 1,
        "wait4": 25,
        "write": 56
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

    