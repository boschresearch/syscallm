# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from app_syscalls import get_redis_syscalls

plt.rcParams["font.family"] = "Times New Roman"

def main():
    syscall_dict = get_redis_syscalls()

    df = pd.DataFrame([
        {'Syscall': syscall, 'Count': count} 
        for syscall, count in syscall_dict.items()
    ])

    plt.figure(figsize=(6, 6.5))

    ax = sns.barplot(df, x='Count', y='Syscall', hue='Syscall', palette='viridis')

    for _, bar in enumerate(ax.patches):
        ax.text(
            bar.get_width() + 0.5,  # Position slightly to the right of the bar
            bar.get_y() + bar.get_height() / 2,  # Center vertically
            f"{int(bar.get_width())}",  # Display the count
            va='center', fontsize=13
        )

    plt.xlabel('Count', fontsize=17)
    plt.ylabel(None)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=13)
    plt.xlim(0, df['Count'].max() + 15)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()

