def read_syscalls(file_path):
    """Read syscalls from a file and return them as a set."""
    with open(file_path, 'r') as file:
        syscalls = {line.strip() for line in file.readlines()}
    return syscalls


def compare_syscalls(base_file, compare_file):
    """Compare syscalls between two files and return added and deleted syscalls."""
    base_syscalls = read_syscalls(base_file)
    compare_syscalls = read_syscalls(compare_file)

    added = compare_syscalls - base_syscalls
    deleted = base_syscalls - compare_syscalls

    return added, deleted


def main():
    # file paths for each Ubuntu version
    kernel_5_4_0 = "/home/jom8be/workspaces/llm-safety-fuzzing/data/syscall/syscalls_5.4.0.txt"
    kernel_5_15_0 = "/home/jom8be/workspaces/llm-safety-fuzzing/data/syscall/syscalls_5.15.0.txt"
    kernel_6_8_0 = "/home/jom8be/workspaces/llm-safety-fuzzing/data/syscall/syscalls_6.8.0.txt"
    kernel_6_11_0 = "/home/jom8be/workspaces/llm-safety-fuzzing/data/syscall/syscalls_6.11.0.txt"

    # compare syscalls between versions
    versions = [("5.4.0", kernel_5_4_0), ("5.15.0", kernel_5_15_0), ("6.8.0", kernel_6_8_0), ("6.11.0", kernel_6_11_0)]

    for i in range(len(versions) - 1):
        base_version, base_file = versions[i]
        compare_version, compare_file = versions[i + 1]

        added, deleted = compare_syscalls(base_file, compare_file)

        print(f"Changes from Ubuntu {base_version} to {compare_version}:")
        print(f"  Added syscalls: {sorted(added)}")
        print(f"  Deleted syscalls: {sorted(deleted)}")


if __name__ == "__main__":
    main()