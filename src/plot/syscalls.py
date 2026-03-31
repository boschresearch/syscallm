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

