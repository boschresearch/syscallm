# Copyright (c) 2025 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

import os
import errno
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec
from itertools import chain
import seaborn as sns
import numpy as np
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config as config
import json
import utils.app_syscalls as app_syscalls

runs = config.runs
modes = config.modes
auts = config.auts
model = "gpt-5.2"
baseline = config.baseline
data_dir = config.data_dir

plt.rcParams["font.family"] = "Times New Roman"
colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B']
failure_types = ['app_crash', 'app_hang', 'error_exit', 'silent_data_corruption']
outcome_types = ['no_changes'] + failure_types
renamed_failure_types = ['App Crash', 'App Hang', 'Error Exit', 'SDC']
renamed_outcome_types = ['No Changes', 'App Crash', 'App Hang', 'Error Exit', 'SDC']

palette = {
    'App Crash': colors[0],
    'App Hang': colors[1],
    'Error Exit': colors[2],
    'SDC': colors[3],
    'No Changes': colors[4]
}


def calculate_failure(data):
    # calculate true counts and percentages for each column
    true_counts = data[outcome_types].sum().astype(int)
    percentages = (true_counts / len(data) * 100).round(2)
    return true_counts, percentages


def calculate_statistics(llm, random):
    # calculate failure counts and percentages grouped by "run"
    llm_counts = llm.groupby(['aut', 'mode', 'run'], group_keys=False).apply(
        lambda group: calculate_failure(group)[1],
        include_groups=False
    )
    random_counts = random.groupby(['aut', 'mode', 'run'], group_keys=False).apply(
        lambda group: calculate_failure(group)[1],
        include_groups=False
    )
    return llm_counts, random_counts


def print_statistics(llm, random):
    # calculate failure counts
    llm_counts, random_counts = calculate_statistics(llm, random)
        
    print(f"---------------------------------------------------------------")
    print(f"SyscaLLM ({model}))")
    print("Counts:")
    print(llm_counts)
    print("Average Counts:")
    print(llm_counts.groupby(['aut', 'mode']).mean().round(2))
    print(f"---------------------------------------------------------------")
    print(f"Random (Log Distribution)")
    print("Counts:")
    print(random_counts)
    print("Average Counts:")
    print(random_counts.groupby(['aut', 'mode']).mean().round(2))


def plot_test_case_distribution(data):
    data = data.copy()

    # sum outcomes by aut, mode, run, syscall
    outcome_sums  = data.groupby(['aut', 'mode', 'run', 'syscall']).sum().reset_index()
    outcome_sums ['total'] = outcome_sums [outcome_types].sum(axis=1)
    
    # drop original outcome columns
    outcome_sums.drop(columns=outcome_types, inplace=True)

    # iterate over unique aut and mode combinations
    for aut in outcome_sums['aut'].unique():
        for mode in outcome_sums['mode'].unique():
            subset = outcome_sums[(outcome_sums['aut'] == aut) & (outcome_sums['mode'] == mode)]

            # filter to only include relevant syscalls
            syscall_dict = app_syscalls.syscall_getters[aut]()
            subset = subset[subset['syscall'].isin(syscall_dict.keys())]

            # ensure all syscalls and runs are present (fill missing with 0)
            full_index = pd.MultiIndex.from_product([range(1, runs + 1), syscall_dict.keys()], names=['run', 'syscall'])
            df = subset.set_index(['run', 'syscall']).reindex(full_index, fill_value=0).reset_index()

            # pivot for plotting
            pivot_df = df.pivot(index='syscall', columns='run', values='total').fillna(0)
            # reverse the order of syscalls for better visualization
            pivot_df = pivot_df.iloc[::-1]

            ax = pivot_df.plot(
                kind='barh',
                figsize=(6, 8),
                color=['#d63b27', '#d6cd27', '#341a9e', '#27d641', '#a02ca0'],
                logx=True,
                width=0.8
            )

            plt.xlabel('Count (log scale)', fontsize=15)
            plt.ylabel(None)
            plt.xticks(fontsize=13)
            plt.yticks(fontsize=13)
            plt.legend(title='Run', fontsize=15, loc='upper right')
            plt.grid(linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(f"figures/test_case_distribution_{aut}_{mode}.png", dpi=300)
            plt.close()


def plot_outcome(llm, random):
    # calculate statistics by group
    llm_counts, random_counts = calculate_statistics(llm, random)

    # add column
    llm_counts['type'] = f'SyscaLLM ({model})'
    random_counts['type'] = 'Random (Log)'
    
    # combine
    df = pd.concat([llm_counts, random_counts], ignore_index=False)

    # convert data type
    df[outcome_types] = df[outcome_types].astype(float)

    # normalize
    df[outcome_types] = df[outcome_types].div(1000).mul(100).round(2)

    # indexes to columns
    df = df.reset_index()

    # melt outcome values
    df = df.melt(
        id_vars=['aut', 'mode', 'run', 'type'],
        value_vars=outcome_types,
        var_name='outcome_type',
        value_name='rate'
    )
    
    # labeling
    outcome_labels = dict(zip(outcome_types, renamed_outcome_types))
    df['outcome_type'] = df['outcome_type'].map(outcome_labels)

    for aut in df['aut'].unique():
        subset = df[df['aut'] == aut].copy()
        plt.figure(figsize=(7, 5))
        sns.lineplot(
            data=subset,
            x='outcome_type',
            y='rate',
            hue='type',
            style='mode',
            markers=True,
            linewidth=2,
            palette={
                f'SyscaLLM ({model})': '#6A5ACD',
                'Random (Log)': '#FF8C00'
            }
        )
        plt.ylabel('Percentage (%)', fontsize=14)
        plt.xlabel(f'{aut}', fontsize=14)
        plt.xticks(rotation=15, fontsize=12)
        plt.yticks(fontsize=12)
        plt.ylim(0, 100)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.savefig(f"figures/outcome_overview_{aut}.png", dpi=300)
        plt.close()


def plot_outcome_per_syscall(llm, random):
    def aggregate_and_compute_failures(df, label):
        agg = df.groupby(['aut', 'mode', 'syscall'])[outcome_types].sum().div(runs).reset_index()
        agg['type'] = label
        
        # compute failure rate %
        agg['failures'] = agg[failure_types].sum(axis=1)
        agg['no_changes'] = agg['no_changes'].fillna(0)
        agg['total'] = agg['failures'] + agg['no_changes']
        # guard against division by zero
        agg['failures'] = agg.apply(
            lambda r: (r['failures'] / r['total'] * 100) if r['total'] > 0 else 0.0,
            axis=1
        ).round(2)

        return agg[['aut', 'mode', 'syscall', 'type', 'failures']]
    
    llm_agg = aggregate_and_compute_failures(llm, f'SyscaLLM ({model})')
    rnd_agg = aggregate_and_compute_failures(random, 'Random (Log)')

    # combine
    all_agg = pd.concat([llm_agg, rnd_agg], ignore_index=True)

    # pivot to desired shape
    pivot = all_agg.pivot_table(
        index="syscall",        # row index
        columns=["aut", "mode", "type"],  # multi-level columns
        values="failures",
        aggfunc="mean"          # or "sum" depending on your metric
    )

    pivot.to_csv("figures/outcome_per_syscall_pivot.csv", sep=",")
    
    # iterate over unique aut and mode combinations
    for (aut, mode), df in all_agg.groupby(['aut', 'mode']):
        # order syscalls alphabetically (stable across both types)
        syscall_order = sorted(df['syscall'].unique())
        df = df.copy()
        df['syscall'] = pd.Categorical(df['syscall'], categories=syscall_order, ordered=True)

        g = sns.catplot(
            data=df,
            kind='point',
            x='failures',
            y='syscall',
            hue='type',
            dodge=True,
            markers='o' if mode == "success" else 'x',
            linestyles='-' if mode == "success" else '--',
            linewidth=1.5,
            height=10,
            aspect=0.6,
            palette={
                f'SyscaLLM ({model})': '#6A5ACD',
                'Random (Log)': '#FF8C00'
            }
        )

        g.set_axis_labels("Failure Rate (%)", None, fontsize=16)
        for ax in g.axes.flat:
            ax.set_ylabel("")
            ax.grid(linestyle='--', alpha=0.5)

        legend = g._legend
        legend.set_title(None)
        legend.set_bbox_to_anchor((0.9, 0.15))
        legend.set_frame_on(True)
        frame = legend.get_frame()
        frame.set_facecolor('white')
        frame.set_edgecolor('lightgrey')
        frame.set_linewidth(0.7)

        plt.tight_layout()
        plt.savefig(f"figures/outcome_per_syscall_{aut}_{mode}.png", dpi=300)
        plt.close()


def plot_outcome_per_syscall_heatmap(llm, random, text: bool = False):
    def aggregate_and_compute_outcomes(df, label, all_syscalls):
        # aggregate each failure type per aut, mode, syscall
        agg = df.groupby(['aut', 'mode', 'syscall'])[outcome_types].sum().div(runs).reset_index()
        agg['type'] = label

        # ensure all syscalls are present for each aut/mode
        result = []
        for aut in agg['aut'].unique():
            for mode in sorted(agg['mode'].unique(), reverse=True):
                # filter for this aut/mode
                aut_mode_df = agg[(agg['aut'] == aut) & (agg['mode'] == mode)]

                # each system call from the total syscalls
                for syscall in all_syscalls:
                    # get the row for this syscall if it exists
                    row = aut_mode_df[aut_mode_df['syscall'] == syscall]

                    if row.empty:
                        # create empty entry with None values
                        entry = {'aut': aut, 'mode': mode, 'syscall': syscall, 'type': label}
                        for failure in failure_types:
                            entry[failure] = None
                        result.append(entry)
                    else:
                        # get the first (and only) row as dict
                        entry = row.iloc[0].to_dict()
                        
                        # total including no_changes
                        row_total = sum([entry[f] if entry[f] is not None else 0 for f in outcome_types])

                        # compute failure rates
                        for failure in failure_types:
                            entry[failure] = (entry[failure] / row_total * 100) if row_total > 0 else None

                        result.append(entry)
        return pd.DataFrame(result, columns=['aut', 'mode', 'syscall', 'type'] + failure_types)

    # get the complete list of syscalls across all auts
    all_syscalls = sorted(set(llm['syscall'].unique()).union(set(random['syscall'].unique())))

    llm_agg = aggregate_and_compute_outcomes(llm, f'SyscaLLM ({model})', all_syscalls)
    rnd_agg = aggregate_and_compute_outcomes(random, 'Random (Log)', all_syscalls)

    # combine
    all_agg = pd.concat([llm_agg, rnd_agg], ignore_index=True)

    # calculate difference between SyscaLLM and Random for each aut, mode, syscall, failure type
    diffs = []
    for aut in all_agg['aut'].unique():
        for mode in all_agg['mode'].unique():
            llm_subset = all_agg[(all_agg['aut'] == aut) & (all_agg['mode'] == mode) & (all_agg['type'] == f'SyscaLLM ({model})')]
            rnd_subset = all_agg[(all_agg['aut'] == aut) & (all_agg['mode'] == mode) & (all_agg['type'] == 'Random (Log)')]
            merged = pd.merge(llm_subset, rnd_subset, on='syscall', suffixes=('_llm', '_rnd'), how='outer')

            diff_dict = {'aut': aut, 'mode': mode, 'syscall': merged['syscall']}
            for failure in failure_types:
                # copy existing values
                diff_dict[f'{failure}_llm'] = merged.get(f'{failure}_llm')
                diff_dict[f'{failure}_rnd'] = merged.get(f'{failure}_rnd')

                # only calculate diff if both llm and rnd exist
                llm_vals = merged[f'{failure}_llm']
                rnd_vals = merged[f'{failure}_rnd']
                diff = []
                for llm_val, rnd_val in zip(llm_vals, rnd_vals):
                    if pd.notnull(llm_val) and pd.notnull(rnd_val):
                        diff.append(round(llm_val - rnd_val, 2))
                    else:
                        diff.append(None)
                diff_dict[f'{failure}_diff'] = pd.Series(diff)
            diffs.append(pd.DataFrame(diff_dict))

    diff_df = pd.concat(diffs, ignore_index=True)

    # calculate syscall counts per AUT and mode from combined llm and random data
    combined_data = pd.concat([llm, random], ignore_index=True)
    syscall_counts = combined_data.groupby(['aut', 'mode', 'syscall']).size().reset_index(name='count')

    n_auts = len(auts)

    fig = plt.figure(figsize=(2.5 * len(diff_df['mode'].unique()) * n_auts + 1.2, 18))
    gs = GridSpec(1, n_auts + 1, figure=fig, width_ratios=[0.08] + [1] * n_auts, wspace=0.0)

    vmin, vmax = -100, 100
    cmap = "RdBu_r"
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    for idx, aut in enumerate(auts):
        aut_df = diff_df[diff_df['aut'] == aut]
        mode_order = sorted(aut_df['mode'].unique(), reverse=True)

        columns = []
        for mode in mode_order:
            columns.append((mode, 'count'))
            for failure in failure_types:
                columns.append((mode, failure))

        pivot_data = {}
        annot_data = {}
        aut_counts = syscall_counts[syscall_counts['aut'] == aut]

        for syscall in all_syscalls:
            row = []
            annot_row = []

            for mode in mode_order:
                count_row = aut_counts[(aut_counts['mode'] == mode) & (aut_counts['syscall'] == syscall)]
                count_val = 0 if count_row.empty else count_row['count'].values[0]

                row.append(count_val)
                annot_row.append(str(int(count_val)))

                mode_df = aut_df[(aut_df['mode'] == mode) & (aut_df['syscall'] == syscall)]
                if mode_df.empty:
                    row.extend([0] * len(failure_types))
                    annot_row.extend([''] * len(failure_types))
                else:
                    for failure in failure_types:
                        val_rnd = mode_df[f'{failure}_rnd'].values[0]
                        val_llm = mode_df[f'{failure}_llm'].values[0]
                        row.append(val_llm - val_rnd)
                        annot_row.append(f"{val_rnd:.0f};{val_llm:.0f}")

            pivot_data[syscall] = row
            annot_data[syscall] = annot_row

        pivot = pd.DataFrame.from_dict(pivot_data, orient='index', columns=pd.MultiIndex.from_tuples(columns))
        annot = pd.DataFrame.from_dict(annot_data, orient='index', columns=pd.MultiIndex.from_tuples(columns))
        pivot = pivot.sort_index()
        annot = annot.loc[pivot.index]

        ax = fig.add_subplot(gs[idx + 1])
        sns.heatmap(
            pivot,
            cmap=cmap,
            center=0,
            vmin=vmin,
            vmax=vmax,
            linewidths=0.5,
            linecolor='lightgrey',
            annot=annot if text else None,
            fmt="",
            cbar=False,
            annot_kws={"fontsize": 10},
            ax=ax,
            yticklabels=False
        )

        n_rows = len(pivot.index)
        count_col_idxs = [i for i, col in enumerate(pivot.columns) if col[1] == 'count']
        for col_idx in count_col_idxs:
            for row_idx in range(n_rows):
                ax.add_patch(
                    Rectangle(
                        (col_idx, row_idx),
                        1,
                        1,
                        facecolor='#F0F8F0',
                        edgecolor='lightgrey',
                        lw=0.5,
                        zorder=3
                    )
                )
                if text:
                    ax.text(
                        col_idx + 0.5,
                        row_idx + 0.5,
                        annot.iloc[row_idx, col_idx],
                        ha='center',
                        va='center',
                        fontsize=10,
                        zorder=4
                    )

        n_xticks = len(pivot.columns)
        ax.text(int(n_xticks * 0.25), -3.5, 'nonnegative', ha='center', va='bottom', fontsize=13)
        ax.text(int(n_xticks * 0.75), -3.5, 'negative', ha='center', va='bottom', fontsize=13)

        ax.set_xticks(np.arange(n_xticks) + 0.5)
        xlabels = []
        for mode in mode_order:
            xlabels.append('Count')
            xlabels.extend(["App\nCrash", "App\nHang", "Error\nExit", "SDC"])
        ax.set_xticklabels(xlabels, rotation=90, fontsize=12)

        ax.xaxis.set_label_position('top')
        ax.xaxis.set_ticks_position('top')

        if idx == 0:
            # first subplot → show y-ticks
            ax.set_yticks(np.arange(len(pivot.index)) + 0.5)
            ax.set_yticklabels(pivot.index, fontsize=13)
            ax.tick_params(axis='y', left=True, labelleft=True)
        else:
            # all other subplots → hide y-ticks
            ax.set_yticks([])
            ax.set_yticklabels([])
            ax.tick_params(axis='y', left=False, labelleft=False)
        ax.set_title(f"{aut.capitalize()}", fontsize=16, fontweight='bold', pad=20)
 
    cbar_ax = fig.add_axes([0.1, 0.025, 0.89, 0.01])
    cbar = fig.colorbar(
        sm,
        cax=cbar_ax,
        orientation='horizontal'
    )
    cbar.set_label("- SyscaLLM + Random (%)", fontsize=14)
    cbar.ax.xaxis.set_ticks_position('bottom')
    cbar.ax.xaxis.set_label_position('bottom')

    plt.subplots_adjust(left=0.07, right=1, top=0.94, bottom=0.04, wspace=0)
    plt.savefig("figures/failure_heatmap.png", dpi=300)
    plt.close()


def plot_failure_per_syscall(llm, random):
    outcome_labels = dict(zip(failure_types, renamed_failure_types))

    def aggregate_data(df, label):
        agg = df.groupby('syscall')[failure_types].sum().div(runs).reset_index()
        agg['type'] = label
        agg.rename(columns=outcome_labels, inplace=True)
        return agg
    
    for aut in llm['aut'].unique():
        for mode in llm['mode'].unique():
            df = pd.DataFrame()

            # aggregate data
            df1 = aggregate_data(llm[(llm['aut'] == aut) & (llm['mode'] == mode)], f'SyscaLLM ({model})')
            df2 = aggregate_data(random[(random['aut'] == aut) & (random['mode'] == mode)], 'Random (Log)')
            df = pd.concat([df1, df2], ignore_index=True)

            # reshape for plotting
            df = df.melt(
                id_vars=['syscall', 'type'],
                value_vars=renamed_failure_types,
                var_name='outcome_type',
                value_name='count'
            )

            # setup subplots with increased height
            fig, axs = plt.subplots(1, len(renamed_failure_types), figsize=(10, 10), sharey=True)

            for i, outcome in enumerate(renamed_failure_types):
                ax = axs[i]
                sub_df = df[df['outcome_type'] == outcome]
                pivot_df = sub_df.pivot_table(
                    index='syscall',
                    columns='type',
                    values='count',
                    fill_value=0
                ).reset_index()

                pivot_df.set_index('syscall').plot(
                    kind='barh',
                    ax=ax,
                    color=['#FF8C00', '#6A5ACD'],
                    legend=(i == len(renamed_failure_types) - 1),
                    logx=(outcome in ['App Crash', 'App Hang', 'Error Exit', 'SDC'])
                )

                ax.set_title(outcome, fontsize=14)
                ax.set_ylabel(None)
                ax.grid(linestyle='--', alpha=0.7)
                ax.invert_yaxis()

                if i == len(renamed_failure_types) - 1:
                    ax.legend(title=None, loc='upper right')

            fig.supxlabel('Count', fontsize=14)
            plt.tight_layout(rect=[0, 0, 1, 0.93])
            plt.savefig(f"figures/failure_per_syscall_{aut}_{mode}.png", dpi=300)
            plt.close()


def plot_silent_data_corruption_by_syscall(llm, random):
    for aut in llm['aut'].unique():
        for mode in llm['mode'].unique():
            subset_llm = llm[(llm['aut'] == aut) & (llm['mode'] == mode)]
            subset_random = random[(random['aut'] == aut) & (random['mode'] == mode)]

            llm_counts = subset_llm[subset_llm['silent_data_corruption'] == True]['syscall'].value_counts()
            random_counts = subset_random[subset_random['silent_data_corruption'] == True]['syscall'].value_counts()

            df = pd.DataFrame({
                'syscall': pd.concat([llm_counts, random_counts]).index,
                'count': pd.concat([llm_counts, random_counts]).values,
                'type': ['Random (Log)'] * len(random_counts) + [f'SyscaLLM ({model})'] * len(llm_counts)
            })
            
            df['count'] = df['count'].fillna(0).astype(int)
            df['count'] = df['count'].div(runs).round(2)

            df['syscall'] = pd.Categorical(df['syscall'], categories=sorted(df['syscall'].unique()), ordered=True)

            plt.figure(figsize=(6, 4))

            sns.barplot(
                data=df,
                x='syscall',
                y='count',
                hue='type',
                palette={f'SyscaLLM ({model})': '#6A5ACD', 'Random (Log)': '#FF8C00'}
            )

            plt.xlabel(None)
            plt.ylabel('Count', fontsize=18)
            plt.xticks(fontsize=12, rotation=15)
            plt.yticks(fontsize=12)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend(fontsize=12)
            plt.tight_layout()
            plt.savefig(f"figures/silent_data_corruption_{aut}_{mode}.png", dpi=300)
            plt.close()


def extract_retval(config_path):
    try:
        with open(config_path, 'r') as file:
            # load json file
            config_data = json.load(file)

            # get strace parameters
            strace_param = config_data['syslog_monitor_config']['faults'][0]

            # get retval value
            retval_start = strace_param.find("retval=") + len("retval=")
            retval_end = strace_param.find(":", retval_start)
            retval = strace_param[retval_start:retval_end]

            return int(retval)
    except Exception:
        return 0
    

def extract_error(config_path):
    try:
        with open(config_path, 'r') as file:
            # load json file
            config_data = json.load(file)

            # get strace parameters
            strace_param = config_data['syslog_monitor_config']['faults'][0]

            # get error value
            error_start = strace_param.find("error=") + len("error=")
            error_end = strace_param.find(":", error_start)
            error_str = strace_param[error_start:error_end]

            if error_str.isdigit():
                error_num = int(error_str)
            else:
                # convert error string to errno number
                error_num = getattr(errno, error_str, 0)

            return error_num
    except Exception:
        return 0
    

def extract_when(config_path):
    try:
        with open(config_path, 'r') as file:
            # load json file
            config_data = json.load(file)

            # get strace parameters
            strace_param = config_data['syslog_monitor_config']['faults'][0]

            # get when value
            when_start = strace_param.find("when=") + len("when=")
            when_end = strace_param.find("..", when_start)
            when = strace_param[when_start:when_end]

            return int(when)
    except Exception:
        return 0
    

def process_dataset(data, mode, config_base, result_types):
    dfs = {}
    for res in result_types:
        df = data[data[res] == True].copy()
        if df.empty:
            df['val'] = pd.Series(dtype=int)
            df['when'] = pd.Series(dtype=int)
        else:
            if mode == "success":
                df['val'] = df.apply(
                    lambda row: extract_retval(f"{config_base}/run{row['run']}/{row['id']}.json"),
                    axis=1
                )
            elif mode == "error_code":
                df['val'] = df.apply(
                    lambda row: extract_error(f"{config_base}/run{row['run']}/{row['id']}.json"),
                    axis=1
                )

            df['when'] = df.apply(
                lambda row: extract_when(f"{config_base}/run{row['run']}/{row['id']}.json"),
                axis=1
            )
        dfs[res] = df
    return dfs


def plot_error_instances_when(aut, mode, llm_config, random_config, llm, random):
    datasets = [
        (f'SyscaLLM ({model})', llm, llm_config),
        ('Random (Log)', random, random_config)
    ]

    # get injected values and when for each failure type
    dfs = {}
    for label, data, config in datasets:
        dataset_dfs = process_dataset(data, mode, config, outcome_types)
        for err, df in dataset_dfs.items():
            # ensure required columns exist even if empty
            if df is None or df.empty:
                df = pd.DataFrame(columns=['syscall', 'val', 'when'])
            dfs[(label, err)] = df

    all_syscalls = sorted(set(
        chain.from_iterable(
            df['syscall'].dropna().unique().tolist()
            for df in dfs.values() if not df.empty
        )
    ), reverse=True)
    syscall_to_y = {name: i for i, name in enumerate(all_syscalls)}

    # collect all 'when' values for color normalization
    all_when = pd.concat([df['when'] for df in dfs.values() if not df['when'].empty], axis=0)
    vmin = all_when.min() if not all_when.empty else 0
    vmax = all_when.max() if not all_when.empty else 1
    cmap = plt.get_cmap('viridis')

    n_cols = len(outcome_types)
    fig, axs = plt.subplots(2, n_cols, figsize=(18, 12), sharex=True, sharey=True)
    scatter_handles = []

    for row, (label, _, _) in enumerate(datasets):
        for col, err in enumerate(outcome_types):
            ax = axs[row, col]
            df = dfs[(label, err)]

            if not df.empty:
                df = df.copy()
                df['y_pos'] = df['syscall'].map(syscall_to_y)

                sc = ax.scatter(
                    df['val'],
                    df['y_pos'],
                    c=df['when'],
                    cmap=cmap,
                    vmin=vmin,
                    vmax=vmax,
                    s=22
                )
                if row == 0 and col == 0:
                    scatter_handles.append(sc)
            else:
                # no data for this panel
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=11, alpha=0.7, transform=ax.transAxes)

            if row == 0:
                ax.set_title(renamed_outcome_types[col], fontsize=14)
            if col == 0:
                ax.set_ylabel(label, fontsize=12)
            else:
                ax.set_ylabel(None)

            ax.set_xlabel(None)
            ax.tick_params(axis='x', labelsize=10)
            ax.tick_params(axis='y', labelsize=10)
            ax.set_xscale('log')
            ax.grid(linestyle='--', alpha=0.6)

            ax.set_yticks(list(syscall_to_y.values()))
            ax.set_yticklabels(list(syscall_to_y.keys()), fontsize=10)

    # shared colorbar for 'when'
    if scatter_handles:
        cbar = fig.colorbar(
            scatter_handles[0], ax=axs, orientation='vertical', fraction=0.05, pad=0.04
        )
        cbar.set_label('when', fontsize=13)
        cbar.ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))

    # shared x-label
    xlabel = 'Error Code (log scale)' if mode == 'error_code' else 'Return Value (log scale)'
    fig.supxlabel(xlabel, fontsize=14)
    plt.savefig(f"figures/error_values_when_{aut}_{mode}.png", dpi=300)
    plt.close()


def plot_error_instances(aut, mode, llm_config, random_config, llm, random):
    datasets = [
        (f'SyscaLLM ({model})', llm, llm_config),
        ('Random (Log)', random, random_config)
    ]

    # get injected values and when for each failure type
    dfs = {}
    for label, data, config in datasets:
        dataset_dfs = process_dataset(data, mode, config, outcome_types)
        for err, df in dataset_dfs.items():
            # ensure required columns exist even if empty
            if df is None or df.empty:
                df = pd.DataFrame(columns=['syscall', 'val'])
            dfs[(label, err)] = df

    all_syscalls = sorted(set(
        chain.from_iterable(
            df['syscall'].dropna().unique().tolist()
            for df in dfs.values() if not df.empty
        )
    ), reverse=True)
    syscall_to_y = {name: i for i, name in enumerate(all_syscalls)}

    n_cols = len(outcome_types)
    fig, axs = plt.subplots(2, n_cols, figsize=(18, 12), sharex=True, sharey=True)
    scatter_handles = []

    for row, (label, _, _) in enumerate(datasets):
        for col, err in enumerate(outcome_types):
            ax = axs[row, col]
            df = dfs[(label, err)]

            if not df.empty:
                df = df.copy()
                df['y_pos'] = df['syscall'].map(syscall_to_y)

                sc = ax.scatter(
                    df['val'],
                    df['y_pos'],
                    s=5,
                    color='black'
                )
                if row == 0 and col == 0:
                    scatter_handles.append(sc)
            else:
                # no data for this panel
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=11, alpha=0.7, transform=ax.transAxes)

            if row == 0:
                ax.set_title(renamed_outcome_types[col], fontsize=14)
            if col == 0:
                ax.set_ylabel(label, fontsize=12)
            else:
                ax.set_ylabel(None)

            ax.set_xlabel(None)
            ax.tick_params(axis='x', labelsize=12)
            ax.set_xscale('log')
            ax.set_yticks(list(syscall_to_y.values()))
            ax.set_yticklabels(list(syscall_to_y.keys()), fontsize=10)
            ax.grid(linestyle='--', alpha=0.6)

    # shared x-label
    xlabel = 'Error Code (log scale)' if mode == 'error_code' else 'Return Value (log scale)'
    fig.supxlabel(xlabel, fontsize=14)
    plt.tight_layout()
    plt.savefig(f"figures/error_values_{aut}_{mode}.png", dpi=300)
    plt.close()


def plot_error_instances_failure(aut, mode, llm_config, random_config, llm, random):
    datasets = [
        (f'SyscaLLM ({model})', llm, llm_config),
        ('Random (Log-Uniform)', random, random_config)
    ]

    # get injected values for all outcomes (merged)
    dfs = {}
    for label, data, config in datasets:
        # collect all rows where any outcome is True
        mask = data[outcome_types].any(axis=1)
        df = data[mask].copy()
        if df.empty:
            df['val'] = pd.Series(dtype=int)
        else:
            if mode == "success":
                df['val'] = df.apply(
                    lambda row: extract_retval(f"{config}/run{row['run']}/{row['id']}.json"),
                    axis=1
                )
            elif mode == "error_code":
                df['val'] = df.apply(
                    lambda row: extract_error(f"{config}/run{row['run']}/{row['id']}.json"),
                    axis=1
                )
        dfs[label] = df

    all_syscalls = sorted(set(
        chain.from_iterable(
            df['syscall'].dropna().unique().tolist()
            for df in dfs.values() if not df.empty
        )
    ), reverse=True)
    syscall_to_y = {name: i for i, name in enumerate(all_syscalls)}

    fig, ax = plt.subplots(figsize=(6, 8))
    color_map = {
        f'SyscaLLM ({model})': '#1F77B4',  # blue
        'Random (Log-Uniform)': '#D62728',  # red
        'Random (Log)': '#D62728',  # red (for consistency if label is 'Random (Log)')
    }
    for label, df in dfs.items():
        if not df.empty:
            df = df.copy()
            df['y_pos'] = df['syscall'].map(syscall_to_y)
            ax.scatter(
                df['val'],
                df['y_pos'],
                s=8,
                label=label,
                alpha=0.7,
                color=color_map.get(label, 'black'),
                marker='o' if 'LLM' in label else 'x'
            )
        else:
            ax.text(0.5, 0.5, f'No data for {label}', ha='center', va='center', fontsize=11, alpha=0.7, transform=ax.transAxes)

    ax.set_yticks(list(syscall_to_y.values()))
    ax.set_yticklabels(list(syscall_to_y.keys()), fontsize=11)
    ax.set_xlabel('Error Code (log scale)' if mode == 'error_code' else 'Return Value (log scale)', fontsize=13)
    ax.set_ylabel(None)
    ax.set_xscale('log')
    ax.grid(linestyle='--', alpha=0.6)
    ax.legend(fontsize=11, ncol=2, bbox_to_anchor=(0.05, 0., 0.9, 1.01), loc='upper center', edgecolor='black')
    plt.tight_layout()
    plt.savefig(f"figures/error_values_{aut}_{mode}_merged.png", dpi=300)
    plt.close()


def plot_cumulative(llm, random):
    llm = llm[llm['run'] == 1].copy()
    random = random[random['run'] == 1].copy()

    llm['aut'] = llm['aut'].str.capitalize()
    random['aut'] = random['aut'].str.capitalize()
    llm['mode'] = llm['mode'].replace({'success': 'Nonnegative', 'error_code': 'Negative'})
    random['mode'] = random['mode'].replace({'success': 'Nonnegative', 'error_code': 'Negative'})

    auts = llm['aut'].unique()
    modes = llm['mode'].unique()
    n_rows = len(auts)
    n_cols = len(modes)

    fig, axs = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=(4 * n_cols, 3.5 * n_rows), sharex=False, sharey=False)
    axs = np.atleast_2d(axs)  # ensure axs is 2D

    color_map = dict(zip(failure_types, colors[:len(failure_types)]))
    legend_labels = []

    for row_idx, aut in enumerate(auts):
        for col_idx, mode in enumerate(modes):
            ax = axs[row_idx, col_idx]

            subset_llm = llm[(llm['aut'] == aut) & (llm['mode'] == mode)].copy()
            subset_random = random[(random['aut'] == aut) & (random['mode'] == mode)].copy()

            subset_llm = subset_llm.sample(n=50, random_state=42) if len(subset_llm) > 50 else subset_llm
            subset_random = subset_random[subset_random['id'].isin(subset_llm['id'])]
            subset_llm = subset_llm.sort_values(by="id")
            subset_random = subset_random.sort_values(by="id")

            for failure in failure_types:
                subset_llm[f"{failure}_llm"] = subset_llm[failure].astype(bool).cumsum()
                subset_random[f"{failure}_rnd"] = subset_random[failure].astype(bool).cumsum()

            subset_llm = subset_llm.drop(columns=failure_types)
            subset_random = subset_random.drop(columns=failure_types)

            merged = pd.merge(
                subset_llm,
                subset_random,
                on=['aut', 'mode', 'run', 'id', 'syscall'],
                how='outer'
            )

            for failure in failure_types:
                line_llm, = ax.plot(
                    merged.index,
                    merged[f"{failure}_llm"],
                    label=f"{failure} (SyscaLLM)",
                    linewidth=2,
                    alpha=0.5,
                    color=color_map[failure]
                )
                line_rnd, = ax.plot(
                    merged.index,
                    merged[f"{failure}_rnd"],
                    label=f"{failure} (Random)",
                    linestyle='dotted',
                    linewidth=2,
                    alpha=0.5,
                    color=color_map[failure]
                )
                if row_idx == 0 and col_idx == 0:
                    legend_labels.extend([line_llm, line_rnd])

            ax.set_title(f"{aut} - {mode}", fontsize=13)
            ax.set_xlabel(None)
            ax.set_ylabel(None)
            ax.grid(linestyle='--', alpha=0.6)
            ax.tick_params(labelsize=12)

    # Add a shared legend at the bottom
    fig.legend(
        handles=legend_labels,
        loc='lower center',
        ncol=2,
        fontsize=12,
        frameon=True,
        bbox_to_anchor=(0.5, 0)
    )

    fig.supxlabel("Number of Injected Errors", fontsize=14, y=0.11)
    fig.supylabel("Cumulative Count", fontsize=14)

    plt.tight_layout(rect=[0, 0.1, 1, 1])  # leave space at bottom for legend
    plt.savefig("figures/cumulative_failure.png", dpi=300)
    plt.close()


def main():    
    # initialize accumulators as empty Series
    all_llm_data = pd.DataFrame() 
    all_random_data = pd.DataFrame()

    for aut in auts:      
        for mode in modes:
            # path to the config files
            llm_config = os.path.join(data_dir, "config", aut, mode, model)
            random_config = os.path.join(data_dir, "config_random_log", aut, mode, model)

            # result directory
            result_dir = os.path.join(data_dir, "result", aut, mode, model)

            for r in range(1, runs + 1):
                # file paths
                llm_generated_file = os.path.join(result_dir, f'result{r}.csv')
                random_generated_file = os.path.join(result_dir, f'result_random_{baseline}{r}.csv')

                # read data
                llm_data = pd.read_csv(llm_generated_file)
                random_data = pd.read_csv(random_generated_file)

                # drop 'timeout' column
                llm_data = llm_data.drop(columns=['timeout'])
                random_data = random_data.drop(columns=['timeout'])

                # add columns
                llm_data['run'] = r
                random_data['run'] = r
                llm_data['aut'] = aut
                random_data['aut'] = aut
                llm_data['mode'] = mode
                random_data['mode'] = mode
                llm_data['syscall'] = llm_data['id'].apply(lambda x: '_'.join(x.split('_')[:-1]))
                random_data['syscall'] = random_data['id'].apply(lambda x: '_'.join(x.split('_')[:-1])  )

                # accumulate all data
                all_llm_data = pd.concat([all_llm_data, llm_data], ignore_index=True)
                all_random_data = pd.concat([all_random_data, random_data], ignore_index=True)

                if r == 1:
                    plot_error_instances_failure(aut, mode, llm_config, random_config, llm_data[(llm_data['aut'] == aut) & (llm_data['mode'] == mode)], random_data[(random_data['aut'] == aut) & (random_data['mode'] == mode)])

    # reorder columns for better readability
    column_order = ['aut', 'mode', 'run', 'id', 'syscall'] + outcome_types
    all_llm_data = all_llm_data[column_order]
    all_random_data = all_random_data[column_order]
            
    # print_statistics(all_llm_data, all_random_data)

    # # plot test case distribution for each aut and mode
    # plot_test_case_distribution(all_llm_data)

    # plot outcome rates for SyscaLLM and Random
    # plot_outcome(all_llm_data, all_random_data)
            
    # # plot failure types by syscall
    # plot_outcome_per_syscall(all_llm_data, all_random_data)

    # plot failure types by syscall with heatmap
    plot_outcome_per_syscall_heatmap(all_llm_data, all_random_data, text=True)

    # # plot failure types by syscall
    # plot_failure_per_syscall(all_llm_data, all_random_data)

    # # plot silent data corruption by syscall
    # plot_silent_data_corruption_by_syscall(all_llm_data, all_random_data)

    # plot cumulative
    # plot_cumulative(all_llm_data, all_random_data)


if __name__ == "__main__":
    main()
