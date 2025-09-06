import os
import errno
from pdb import run
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config as config
import json
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


def plot_error_instances(aut, mode, llm_config, random_config, llm, random):
    datasets = [
        ('SyscaLLM (GPT-4o)', llm, llm_config),
        ('Random (Log)', random, random_config)
    ]

    dfs = {}
    for label, data, config in datasets:
        dataset_dfs = process_dataset(data, mode, config, failure_types)
        for err, df in dataset_dfs.items():
            dfs[(label, err)] = df

    # get unique syscalls
    all_syscalls = pd.concat([llm, random])
    unique_syscalls = sorted(all_syscalls['syscall'].unique().tolist())
    
    for df in dfs.values():
        df['syscall'] = pd.Categorical(df['syscall'], categories=unique_syscalls, ordered=True)

    fig, axs = plt.subplots(2, 4, figsize=(18, 10), sharex=True, sharey=True)
    for row, (label, _, _) in enumerate(datasets):
        for col, err in enumerate(failure_types):
            ax = axs[row, col]
            df = dfs[(label, err)]

            scatter = sns.scatterplot(
                data=df,
                x='val',
                y='syscall',
                hue='when',
                palette='viridis',
                legend=(row == 0 and col == len(failure_types) - 1),
                ax=ax
            )
            if row == 0:
                ax.set_title(renamed_failure_types[col], fontsize=14)
            if col == 0:
                ax.set_ylabel(label, fontsize=13)
            else:
                ax.set_ylabel(None)
            ax.set_xlabel(None)
            ax.tick_params(axis='x', labelsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.set_xscale('log')
            ax.grid(linestyle='--', alpha=0.7)

    handles, labels = axs[0, -1].get_legend_handles_labels()
    fig.legend(handles, labels, title='when', loc='upper right', bbox_to_anchor=(1.04, 0.95), fontsize=12, title_fontsize=13)

    fig.supxlabel('Return Value (log scale)', fontsize=15)
    xlabel = 'Error Code (log scale)' if mode == 'error_code' else 'Return Value (log scale)'
    fig.supxlabel(xlabel, fontsize=15)
    plt.savefig(f"figures/error_values_{aut}_{mode}.png", dpi=300)
    plt.close()


def plot_error_instances_no_changes(aut, mode, llm_config, random_config, llm, random):
    df1 = process_dataset(llm, mode, llm_config, ['no_changes'])['no_changes']
    df2 = process_dataset(random, mode, random_config, ['no_changes'])['no_changes']

    # get unique syscalls
    all_syscalls = pd.concat([llm, random])
    unique_syscalls = sorted(all_syscalls['syscall'].unique().tolist())

    for df in [df1, df2]:
        df['syscall'] = pd.Categorical(df['syscall'], categories=unique_syscalls, ordered=True)

    fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)

    for ax, df, title in zip(axs, [df1, df2], ['SyscaLLM (GPT-4o)', 'Random (Log)']):
        sns.scatterplot(
            data=df,
            x='val',
            y='syscall',
            hue='when',
            palette='viridis',
            legend=True,
            ax=ax
        )
        ax.set_title(title, fontsize=14)
        ax.set_xlabel(None)
        ax.set_ylabel(None)
        ax.tick_params(axis='x', labelsize=12)
        ax.tick_params(axis='y', labelsize=12)
        ax.set_xscale('log')
        ax.grid(linestyle='--', alpha=0.7)
        # ax.get_legend().remove()

    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, title='when', loc='upper left', bbox_to_anchor=(0.9, 0.95))
    fig.supxlabel('Return Value for No Changes (log scale)', fontsize=14)
    plt.tight_layout(pad=1.0, w_pad=0.5, h_pad=0.5, rect=[0, 0, 0.9, 1])
    plt.savefig(f"figures/no_changes_{aut}_{mode}.png", dpi=300)
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
            
            plot_error_instances(aut, mode, llm_config, random_config, llm_data, random_data)
            plot_error_instances_no_changes(aut, mode, llm_config, random_config, llm_data, random_data)

    # reorder columns for better readability
    column_order = ['aut', 'mode', 'run', 'id', 'syscall'] + outcome_types
    all_llm_data = all_llm_data[column_order]
    all_random_data = all_random_data[column_order]
            
    print_statistics(all_llm_data, all_random_data)

    # plot test case distribution for each aut and mode
    # plot_test_case_distribution(all_llm_data)

    # plot outcome rates for SyscaLLM (GPT-4o) and Random
    plot_outcome(all_llm_data, all_random_data)
            
    # plot normalized failure types by syscall
    plot_outcome_per_syscall(all_llm_data, all_random_data)

    # plot failure types by syscall
    plot_failure_per_syscall(all_llm_data, all_random_data)

    # plot silent data corruption by syscall
    plot_silent_data_corruption_by_syscall(all_llm_data, all_random_data)


if __name__ == "__main__":
    main()
