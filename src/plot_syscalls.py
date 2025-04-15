import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from app_syscalls import get_app_syscalls

plt.rcParams["font.family"] = "Times New Roman"

def main():
    syscall_dict = get_app_syscalls()

    df = pd.DataFrame([
        {'Syscall': syscall, 'Count': count} 
        for syscall, count in syscall_dict.items()
    ])

    plt.figure(figsize=(6, 6.5))

    sns.barplot(df, x='Count', y='Syscall', hue='Syscall', palette='viridis')

    plt.xlabel('Count', fontsize=14)
    plt.ylabel(None)
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()

