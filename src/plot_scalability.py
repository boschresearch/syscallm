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
    ubuntu_18_04 = "/home/jom8be/workspaces/llm-safety-fuzzing/data/syscall/ubuntu_18.04.6_syscalls.txt"
    ubuntu_20_04 = "/home/jom8be/workspaces/llm-safety-fuzzing/data/syscall/ubuntu_20.04.6_syscalls.txt"
    ubuntu_22_04 = "/home/jom8be/workspaces/llm-safety-fuzzing/data/syscall/ubuntu_22.04.6_syscalls.txt"
    ubuntu_24_04 = "/home/jom8be/workspaces/llm-safety-fuzzing/data/syscall/ubuntu_24.04.2_syscalls.txt"

    # compare syscalls between versions
    versions = [("18.04", ubuntu_18_04), ("20.04", ubuntu_20_04), ("22.04", ubuntu_22_04), ("24.04", ubuntu_24_04)]

    for i in range(len(versions) - 1):
        base_version, base_file = versions[i]
        compare_version, compare_file = versions[i + 1]

        added, deleted = compare_syscalls(base_file, compare_file)

        print(f"Changes from Ubuntu {base_version} to {compare_version}:")
        print(f"  Added syscalls: {sorted(added)}")
        print(f"  Deleted syscalls: {sorted(deleted)}")


if __name__ == "__main__":
    main()