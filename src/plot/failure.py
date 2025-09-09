import os
import errno
import pandas as pd
import matplotlib.pyplot as plt
from itertools import chain
import seaborn as sns
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config as config
import json
import matplotlib as mpl
import utils.app_syscalls as app_syscalls

runs = config.runs
modes = config.modes
auts = config.auts
baseline = config.baseline
data_dir = config.data_dir

temperature = "0.5"

plt.rcParams["font.family"] = "Times New Roman"
colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B']
failure_types = ['app_crash', 'app_hang', 'error_exit', 'silent_data_corruption']
outcome_types = ['no_changes'] + failure_types
renamed_failure_types = ['App Crash', 'App Hang', 'Error Exit', 'Silent Data Corruption']
renamed_outcome_types = ['No Changes', 'App Crash', 'App Hang', 'Error Exit', 'Silent Data Corruption']

palette = {
    'App Crash': colors[0],
    'App Hang': colors[1],
    'Error Exit': colors[2],
    'Silent Data Corruption': colors[3],
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
        lambda group: calculate_failure(group)[0],
        include_groups=False
    )
    random_counts = random.groupby(['aut', 'mode', 'run'], group_keys=False).apply(
        lambda group: calculate_failure(group)[0],
        include_groups=False
    )
    return llm_counts, random_counts


def print_statistics(llm, random):
    # calculate failure counts
    llm_counts, random_counts = calculate_statistics(llm, random)
        
    print(f"---------------------------------------------------------------")
    print(f"SyscaLLM (GPT-4o)")
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
    llm_counts['type'] = 'SyscaLLM (GPT-4o)'
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
                'SyscaLLM (GPT-4o)': '#6A5ACD',
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
    
    llm_agg = aggregate_and_compute_failures(llm, 'SyscaLLM (GPT-4o)')
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
                'SyscaLLM (GPT-4o)': '#6A5ACD',
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


def plot_outcome_per_syscall_heatmap(llm, random):
    def aggregate_and_compute_outcomes(df, label, all_syscalls):
        # aggregate each failure type per aut, mode, syscall
        agg = df.groupby(['aut', 'mode', 'syscall'])[failure_types].sum().div(runs).reset_index()
        agg['type'] = label

        # ensure all syscalls are present for each aut/mode
        result = []
        for aut in agg['aut'].unique():
            for mode in agg['mode'].unique():
                aut_mode_df = agg[(agg['aut'] == aut) & (agg['mode'] == mode)]
                for syscall in all_syscalls:
                    row = aut_mode_df[aut_mode_df['syscall'] == syscall]
                    if row.empty:
                        entry = {'aut': aut, 'mode': mode, 'syscall': syscall, 'type': label}
                        for failure in failure_types:
                            entry[failure] = None
                        entry['total'] = None
                        result.append(entry)
                    else:
                        entry = row.iloc[0].to_dict()
                        row_total = sum([entry[f] if entry[f] is not None else 0 for f in failure_types])
                        for failure in failure_types:
                            entry[failure] = (entry[failure] / row_total * 100) if row_total > 0 else None
                        entry['total'] = sum([entry[f] if entry[f] is not None else 0 for f in failure_types])
                        result.append(entry)
        return pd.DataFrame(result, columns=['aut', 'mode', 'syscall', 'type', 'total'] + failure_types)

    # get the complete list of syscalls across all auts
    all_syscalls = sorted(set(llm['syscall'].unique()).union(set(random['syscall'].unique())))

    llm_agg = aggregate_and_compute_outcomes(llm, 'SyscaLLM (GPT-4o)', all_syscalls)
    rnd_agg = aggregate_and_compute_outcomes(random, 'Random (Log)', all_syscalls)

    # combine
    all_agg = pd.concat([llm_agg, rnd_agg], ignore_index=True)

    # calculate difference between SyscaLLM and Random for each aut, mode, syscall, failure type
    diffs = []
    for aut in all_agg['aut'].unique():
        for mode in all_agg['mode'].unique():
            llm_subset = all_agg[(all_agg['aut'] == aut) & (all_agg['mode'] == mode) & (all_agg['type'] == 'SyscaLLM (GPT-4o)')]
            rnd_subset = all_agg[(all_agg['aut'] == aut) & (all_agg['mode'] == mode) & (all_agg['type'] == 'Random (Log)')]
            merged = pd.merge(llm_subset, rnd_subset, on='syscall', suffixes=('_llm', '_rnd'), how='outer')

            diff_dict = {'aut': aut, 'mode': mode, 'syscall': merged['syscall']}
            for failure in failure_types + ['total']:
                diff_dict[f'{failure}_llm'] = merged.get(f'{failure}_llm')
                diff_dict[f'{failure}_rnd'] = merged.get(f'{failure}_rnd')
                diff_dict[f'{failure}_diff'] = (
                    merged[f'{failure}_llm'].fillna(0) - merged[f'{failure}_rnd'].fillna(0)
                ).round(2)
            diffs.append(pd.DataFrame(diff_dict))

    diff_df = pd.concat(diffs, ignore_index=True)
    diff_df.to_csv("figures/outcome_per_syscall_diff.csv", index=False)

    # Now plot per aut, with all failures for each mode
    for aut in diff_df['aut'].unique():
        aut_df = diff_df[diff_df['aut'] == aut]
        # Create a multi-index columns: (mode, failure)
        columns = []
        for mode in aut_df['mode'].unique():
            for failure in failure_types:
                columns.append((mode, failure))
        # Build pivot table for heatmap values and for annotations
        pivot_data = {}
        annot_data = {}
        for syscall in aut_df['syscall'].unique():
            row = []
            annot_row = []
            for mode in aut_df['mode'].unique():
                mode_df = aut_df[(aut_df['mode'] == mode) & (aut_df['syscall'] == syscall)]
                for failure in failure_types:
                    val_rnd = mode_df[f'{failure}_rnd'].values[0] if not mode_df.empty and pd.notnull(mode_df[f'{failure}_rnd'].values[0]) else 0
                    val_llm = mode_df[f'{failure}_llm'].values[0] if not mode_df.empty and pd.notnull(mode_df[f'{failure}_llm'].values[0]) else 0
                    diff_val = val_llm - val_rnd
                    row.append(diff_val)
                    annot_row.append(f"{val_rnd:.1f}, {val_llm:.1f}")
            pivot_data[syscall] = row
            annot_data[syscall] = annot_row
        pivot = pd.DataFrame.from_dict(pivot_data, orient='index', columns=pd.MultiIndex.from_tuples(columns))
        annot = pd.DataFrame.from_dict(annot_data, orient='index', columns=pd.MultiIndex.from_tuples(columns))
        pivot = pivot.sort_index()
        annot = annot.loc[pivot.index]

        plt.figure(figsize=(5 + 2 * len(aut_df['mode'].unique()), 12))
        ax = sns.heatmap(
            pivot,
            cmap="RdBu_r",
            center=0,
            linewidths=0.5,
            linecolor='lightgrey',
            annot=annot,
            fmt="",
            cbar_kws={"label": f"SyscaLLM - Random (%)"}
        )
        plt.title(f"{aut}", fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(fontsize=8)
        plt.tight_layout()
        plt.savefig(f"figures/{aut}_diff_heatmap.png", dpi=300)
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
            df1 = aggregate_data(llm[(llm['aut'] == aut) & (llm['mode'] == mode)], 'SyscaLLM (GPT-4o)')
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
                    logx=(outcome in ['App Crash', 'App Hang', 'Error Exit', 'Silent Data Corruption'])
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
                'type': ['Random (Log)'] * len(random_counts) + ['SyscaLLM (GPT-4o)'] * len(llm_counts)
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
                palette={'SyscaLLM (GPT-4o)': '#6A5ACD', 'Random (Log)': '#FF8C00'}
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
        ('SyscaLLM (GPT-4o)', llm, llm_config),
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
        ('SyscaLLM (GPT-4o)', llm, llm_config),
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
            ax.tick_params(axis='x', labelsize=10)
            ax.tick_params(axis='y', labelsize=10)
            ax.set_xscale('log')
            ax.grid(linestyle='--', alpha=0.6)

            ax.set_yticks(list(syscall_to_y.values()))
            ax.set_yticklabels(list(syscall_to_y.keys()), fontsize=10)

    # shared x-label
    xlabel = 'Error Code (log scale)' if mode == 'error_code' else 'Return Value (log scale)'
    fig.supxlabel(xlabel, fontsize=14)
    plt.savefig(f"figures/error_values_{aut}_{mode}.png", dpi=300)
    plt.close()


def main():    
    # initialize accumulators as empty Series
    all_llm_data = pd.DataFrame() 
    all_random_data = pd.DataFrame()

    for aut in auts:      
        for mode in modes:
            # path to the config files
            llm_config = os.path.join(data_dir, "config", aut, mode, f"temperature_{temperature}", "gpt-4o")
            random_config = os.path.join(data_dir, "config_random_log", aut, mode, f"temperature_{temperature}", "gpt-4o")

            # result directory
            result_dir = os.path.join(data_dir, "result", aut, mode)

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
                    plot_error_instances(aut, mode, llm_config, random_config, llm_data[(llm_data['aut'] == aut) & (llm_data['mode'] == mode)], random_data[(random_data['aut'] == aut) & (random_data['mode'] == mode)])

    # reorder columns for better readability
    column_order = ['aut', 'mode', 'run', 'id', 'syscall'] + outcome_types
    all_llm_data = all_llm_data[column_order]
    all_random_data = all_random_data[column_order]
            
    # print_statistics(all_llm_data, all_random_data)

    # plot test case distribution for each aut and mode
    plot_test_case_distribution(all_llm_data)

    # plot outcome rates for SyscaLLM (GPT-4o) and Random
    plot_outcome(all_llm_data, all_random_data)
            
    # plot failure types by syscall
    plot_outcome_per_syscall(all_llm_data, all_random_data)

    # plot failure types by syscall with heatmap
    plot_outcome_per_syscall_heatmap(all_llm_data, all_random_data)

    # plot failure types by syscall
    plot_failure_per_syscall(all_llm_data, all_random_data)

    # plot silent data corruption by syscall
    plot_silent_data_corruption_by_syscall(all_llm_data, all_random_data)


if __name__ == "__main__":
    main()
