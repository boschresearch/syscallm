import csv

def extract_syscalls_from_csv():
    # TODO: Better path handling
    file_path = "/home/jom8be/workspace/syscallm/safety-fuzzing/examples/export/output.oracle.csv"
    syscall_count = dict()
    
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if reader.line_num == 1:
                header = row
                column_index = header.index("syscall")
            else:
                syscall = row[column_index]
                syscall_count[syscall] = syscall_count.get(syscall, 0) + 1

    return dict(sorted(syscall_count.items()))
    return {
        "access": 1,
        "arch_prctl": 1,
        "brk": 8,
        "close": 44,
        "dup": 3,
        "execve": 1,
        "exit_group": 1,
        "fcntl": 3,
        "futex": 14,
        "getcwd": 12,
        "getdents64": 16,
        "getegid": 1,
        "geteuid": 1,
        "getgid": 1,
        "getpid": 1,
        "getrandom": 2,
        "getuid": 1,
        "ioctl": 30,
        "lseek": 50,
        "mmap": 40,
        "mprotect": 8,
        "munmap": 2,
        "newfstatat": 221,
        "openat": 57,
        "pread64": 2,
        "prlimit64": 1,
        "read": 57,
        "readlink": 7,
        "rseq": 1,
        "rt_sigaction": 66,
        "set_robust_list": 1,
        "set_tid_address": 1,
        "sysinfo": 1,
        "write": 2
    }

def get_redis_syscalls():
    return {
        "accept4": 18,
        "access": 19,
        "arch_prctl": 18,
        "bind": 2,
        "brk": 57,
        "chdir": 1,
        "clock_nanosleep": 1,
        "clone": 21,
        "clone3": 5,
        "close": 234,
        "connect": 22,
        "dup2": 18,
        "epoll_create": 1,
        "epoll_ctl": 22,
        "epoll_wait": 67,
        "execve": 18,
        "exit_group": 19,
        "fadvise64": 3,
        "fcntl": 54,
        "fdatasync": 2,
        "fsync": 2,
        "futex": 26,
        "getcwd": 2,
        "getegid": 1,
        "geteuid": 2,
        "getgid": 1,
        "getpeername": 1,
        "getpid": 49,
        "getppid": 1,
        "getrandom": 20,
        "getsockopt": 2,
        "getuid": 1,
        "ioctl": 47,
        "kill": 1,
        "listen": 2,
        "lseek": 6,
        "madvise": 22,
        "mkdir": 2,
        "mmap": 415,
        "mprotect": 99,
        "munmap": 79,
        "newfstatat": 178,
        "open": 22,
        "openat": 140,
        "pipe2": 14,
        "poll": 11,
        "prctl": 5,
        "pread64": 36,
        "prlimit64": 22,
        "read": 255,
        "readlink": 11,
        "recvfrom": 34,
        "rename": 2,
        "rseq": 23,
        "rt_sigaction": 48,
        "rt_sigprocmask": 31,
        "rt_sigreturn": 19,
        "rt_sigsuspend": 1,
        "sched_getaffinity": 12,
        "sendto": 34,
        "set_robust_list": 39,
        "set_tid_address": 18,
        "setitimer": 1,
        "setsockopt": 93,
        "sigaltstack": 2,
        "socket": 13,
        "statfs": 2,
        "sysinfo": 3,
        "umask": 4,

if __name__ == "__main__":
    syscall_count = extract_syscalls_from_csv()
    
    for syscall, count in syscall_count.items():
        print(f"\"{syscall}\": {count},")