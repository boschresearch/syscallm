import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import utils.config as config
import json
from app_syscalls import get_redis_syscalls

plt.rcParams["font.family"] = "Times New Roman"
colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B']
failure_types = ['app_crash', 'app_hang', 'error_exit', 'silent_data_corruption']
outcome_types = ['no_changes'] + failure_types
renamed_outcome_types = ['No Changes', 'App Crash', 'App Hang', 'Error Exit', 'Silent Data Corruption']
missing_syscalls = ['rseq', 'clock_adjtime', 'epoll_ctl_old', 'epoll_wait_old', 'io_pgetevents', 'timerfd']

palette = {
    'App Crash': colors[0],
    'App Hang': colors[1],
    'Error Exit': colors[2],
    'Silent Data Corruption': colors[3],
    'No Changes': colors[4]
}

runs = config.runs

def read_data(llm_file, random_file):
    # read data from CSV files
    llm_data = pd.read_csv(llm_file)
    random_data = pd.read_csv(random_file)

    return llm_data, random_data


def add_run_column(data, run):
    # add a 'run' column to the data
    data['run'] = run
    return data


def add_syscall_column(data):
    # add a 'syscall' column based on the 'id' column
    data['syscall'] = data['id'].apply(lambda x: '_'.join(x.split('_')[:-1]))
    return data


def calculate_failure(data):
    # calculate true counts and percentages for each column
    true_counts = data[outcome_types].sum().astype(int)
    percentages = (true_counts / len(data) * 100).round(2)
    return true_counts, percentages


def calculate_statistics(llm, random):
    # calculate failure counts and percentages grouped by "run"
    llm_counts = llm.groupby('run', group_keys=False).apply(
        lambda group: calculate_failure(group)[0],
        include_groups=False
    )
    llm_percentages = llm.groupby('run', group_keys=False).apply(
        lambda group: calculate_failure(group)[1],
        include_groups=False
    )
    random_counts = random.groupby('run', group_keys=False).apply(
        lambda group: calculate_failure(group)[0],
        include_groups=False
    )
    random_percentages = random.groupby('run', group_keys=False).apply(
        lambda group: calculate_failure(group)[1],
        include_groups=False
    )
    return llm_counts, llm_percentages, random_counts, random_percentages


def print_statistics(llm, random):
    # calculate failure counts and percentages
    llm_counts, llm_percentages, random_counts, random_percentages = calculate_statistics(llm, random)

    # average count and percentage across runs
    avg_llm_percentages = llm_percentages.mean().round(2)
    avg_random_percentages = random_percentages.mean().round(2)
    
    print(f"Total test counts for each {llm['run'].value_counts()}")    
    print(f"---------------------------------------------------------------")
    print(f"SyscaLLM (GPT-4o)-Generated")
    print("Counts:")
    print(llm_counts)
    print("Percentages:")
    print(llm_percentages)
    print("Average Counts:")
    print(llm_counts.mean().round(2).to_frame().T)
    print("Average Percentages:")
    print(avg_llm_percentages.to_frame().T)
    print(f"---------------------------------------------------------------")
    print(f"Random-Generated")
    print("Counts:")
    print(random_counts)
    print("Percentages:")
    print(random_percentages)
    print("Average Counts:")
    print(random_counts.mean().round(2).to_frame().T)
    print("Average Percentages:")
    print(avg_random_percentages.to_frame().T)
    print(f"---------------------------------------------------------------")


def print_silent_data_corruption_syscalls(llm, random):
    for run in range(1, runs + 1):
        llm_silent_data_corruption = llm[(llm['run'] == run) & (llm['silent_data_corruption'] == True)]['syscall'].unique()
        random_silent_data_corruption = random[(random['run'] == run) & (random['silent_data_corruption'] == True)]['syscall'].unique()
        print(f"Run {run}:")
        print(f"Unique syscalls with silent data corruption (SyscaLLM (GPT-4o)): {llm_silent_data_corruption}")
        print(f"Unique syscalls with silent data corruption (Random): {random_silent_data_corruption}")


def plot_outcome_per_syscall(data1, data2):
    def aggregate_and_compute_failures(df, label):
        agg = df.groupby('syscall')[outcome_types].sum().div(runs).reset_index()
        agg['type'] = label
        agg['failures'] = agg[failure_types].sum(axis=1)
        agg['no_changes'] = agg['no_changes'].fillna(0)
        agg['total'] = agg['failures'] + agg['no_changes']
        agg['failures'] = agg['failures'].div(agg['total']).mul(100).round(2)
        return agg[['syscall', 'type', 'failures']]
    
    df1 = aggregate_and_compute_failures(data1, 'SyscaLLM (GPT-4o)')
    df2 = aggregate_and_compute_failures(data2, 'Random')
        
    df = pd.concat([df1, df2], ignore_index=True)
    
    # sort syscalls alphabetically
    syscall_order = sorted(df['syscall'].unique())
    df['syscall'] = pd.Categorical(df['syscall'], categories=syscall_order, ordered=True)

    # plot
    g = sns.catplot(
        data=df,
        kind='point',
        x='failures',
        y='syscall',
        hue='type',
        dodge=True,
        markers=['o', 'x'],
        linestyles=['-', '--'],
        linewidth=1.5,
        height=6,
        aspect=0.7,
        palette={
            'SyscaLLM (GPT-4o)': '#6A5ACD',
            'Random': '#FF8C00'
        }
    )

    # axis labels and formatting
    g.set_axis_labels("Failure Rate (%)", None, fontsize=16)
    for ax in g.axes.flat:
        ax.set_ylabel("")
        ax.grid(linestyle='--', alpha=0.5)

    # style legend
    legend = g._legend
    legend.set_title(None)
    legend.set_bbox_to_anchor((1, 0.15))
    legend.set_frame_on(True)
    frame = legend.get_frame()
    frame.set_facecolor('white')
    frame.set_edgecolor('lightgrey')
    frame.set_linewidth(0.7)

    plt.tight_layout()
    plt.show()


def plot_failure_per_syscall(data1, data2):
    titles = ['App Crash', 'App Hang', 'Error Exit', 'Silent Data Corruption']
    outcome_labels = dict(zip(failure_types, titles))

    def aggregate_data(df, label):
        agg = df.groupby('syscall')[failure_types].sum().div(runs).reset_index()
        agg['type'] = label
        agg.rename(columns=outcome_labels, inplace=True)
        return agg

    # aggregate data
    df1 = aggregate_data(data1, 'SyscaLLM (GPT-4o)')
    df2 = aggregate_data(data2, 'Random')
    df = pd.concat([df1, df2], ignore_index=True)

    # reshape for plotting
    df = df.melt(
        id_vars=['syscall', 'type'],
        value_vars=titles,
        var_name='outcome_type',
        value_name='count'
    )

    # setup subplots
    fig, axs = plt.subplots(1, len(titles), figsize=(10, 6), sharey=True)

    for i, outcome in enumerate(titles):
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
            legend=(i == len(titles) - 1),
            logx=(outcome in ['App Crash', 'App Hang', 'Error Exit'])
        )

        ax.set_title(outcome, fontsize=14)
        ax.set_ylabel(None)
        ax.grid(linestyle='--', alpha=0.7)
        ax.invert_yaxis()

        if i == len(titles) - 1:
            ax.legend(title=None, loc='upper right')

    fig.supxlabel('Count', fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.show()


def plot_silent_data_corruption_by_syscall(llm, random):
    llm_counts = llm[llm['silent_data_corruption'] == True]['syscall'].value_counts()
    random_counts = random[random['silent_data_corruption'] == True]['syscall'].value_counts()

    df = pd.DataFrame({
        'syscall': pd.concat([llm_counts, random_counts]).index,
        'count': pd.concat([llm_counts, random_counts]).values,
        'type': ['Random'] * len(random_counts) + ['SyscaLLM (GPT-4o)'] * len(llm_counts)
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
        palette={'SyscaLLM (GPT-4o)': '#6A5ACD', 'Random': '#FF8C00'}
    )

    plt.xlabel(None)
    plt.ylabel('Count', fontsize=18)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.show()


def plot_outcome(data1, data2):
    # compute total test cases per run
    total_count = data1['run'].value_counts()

    # aggregate outcomes
    def aggregate_outcomes(df, label):
        counts = df[outcome_types].groupby(df['run']).sum().reset_index()
        counts['type'] = label
        return counts
    
    llm_counts = aggregate_outcomes(data1, 'SyscaLLM (GPT-4o)')
    random_counts = aggregate_outcomes(data2, 'Random')

    # combine and normalize
    df = pd.concat([llm_counts, random_counts], ignore_index=True)
    df[outcome_types] = df[outcome_types].astype(float)

    for run in range(1, runs + 1):
        if run in total_count:
            total = total_count[run]
            df.loc[df['run'] == run, outcome_types] = (
                df.loc[df['run'] == run, outcome_types] / total * 100
            )
    
    # prepare for plotting
    outcome_labels = dict(zip(outcome_types, renamed_outcome_types))

    df = df.melt(
        id_vars=['run', 'type'],
        value_vars=outcome_types,
        var_name='outcome_type',
        value_name='rate'
    )
    df['outcome_type'] = df['outcome_type'].map(outcome_labels)

    plt.figure(figsize=(5, 4))

    sns.lineplot(
        data=df,
        x='outcome_type',
        y='rate',
        hue='type',
        style='type',
        markers=True,
        linewidth=2,
        palette={
            'SyscaLLM (GPT-4o)': '#6A5ACD',
            'Random': '#FF8C00'
        }
    )

    plt.ylabel('Percentage (%)', fontsize=14)
    plt.xlabel('Outcome', fontsize=14)
    plt.xticks(rotation=15, fontsize=12)
    plt.yticks(fontsize=12)
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.show()


def plot_test_case_distribution(data):
    data = data.copy()

    # sum outcomes by run and syscall
    outcome_sums  = data.groupby(['run', 'syscall']).sum().reset_index()
    outcome_sums ['total'] = outcome_sums [outcome_types].sum(axis=1)
    
    # drop original outcome columns
    outcome_sums.drop(columns=outcome_types, inplace=True)

    # filter to only include relevant syscalls
    syscall_dict = get_redis_syscalls()
    outcome_sums = outcome_sums[outcome_sums['syscall'].isin(syscall_dict.keys())]

    # ensure all syscalls and runs are present (fill missing with 0)
    full_index = pd.MultiIndex.from_product([range(1, runs + 1), syscall_dict.keys()], names=['run', 'syscall'])
    df = outcome_sums.set_index(['run', 'syscall']).reindex(full_index, fill_value=0).reset_index()

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

    # highlight syscalls that are missing man pages
    for label in ax.get_yticklabels():
        syscall = label.get_text()
        if syscall in missing_syscalls:
            label.set_fontstyle('italic')
            label.set_color('red')
            label.set_alpha(0.7)
            label.set_text(f"{syscall} (X)")

    plt.xlabel('Count (log scale)', fontsize=15)
    plt.ylabel(None)
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.legend(title='Run', fontsize=15, loc='upper right')
    plt.grid(linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def extract_retval(config_path):
    try:
        with open(config_path, 'r') as file:
            config_data = json.load(file)
            strace_param = config_data['syslog_monitor_config']['faults'][0]
            retval_start = strace_param.find("retval=") + len("retval=")
            retval_end = strace_param.find(":", retval_start)
            retval = strace_param[retval_start:retval_end]
            return int(retval)
    except Exception:
        return 0
    

def extract_when(config_path):
    try:
        with open(config_path, 'r') as file:
            config_data = json.load(file)
            strace_param = config_data['syslog_monitor_config']['faults'][0]
            when_start = strace_param.find("when=") + len("when=")
            when_end = strace_param.find("..", when_start)
            when = strace_param[when_start:when_end]
            return int(when)
    except Exception:
        return 0
    

def process_dataset(data, config_base, result_types):
    dfs = {}
    for res in result_types:
        df = data[data[res] == True].copy()
        if df.empty:
            df['retval'] = pd.Series(dtype=int)
        else:
            df['retval'] = df.apply(
                lambda row: extract_retval(f"{config_base}/run{row['run']}/{row['id']}.json"),
                axis=1
            )
            df['when'] = df.apply(
                lambda row: extract_when(f"{config_base}/run{row['run']}/{row['id']}.json"),
                axis=1
            )
        dfs[res] = df
    return dfs


def plot_error_instances(data1, data2):
    llm_config = "/home/jom8be/workspaces/data/config/gpt-4o"
    random_config = "/home/jom8be/workspaces/data/config_random_log/gpt-4o"

    error_types = ['app_crash', 'app_hang', 'error_exit', 'silent_data_corruption']
    titles = ['App Crash', 'App Hang', 'Error Exit', 'Silent Data Corruption']
    datasets = [
        ('SyscaLLM (GPT-4o)', data1, llm_config),
        ('Random', data2, random_config)
    ]

    dfs = {}
    for label, data, config in datasets:
        dataset_dfs = process_dataset(data, config, error_types)
        for err, df in dataset_dfs.items():
            dfs[(label, err)] = df

    # get unique syscalls
    all_syscalls = pd.concat([data1, data2])
    unique_syscalls = sorted(all_syscalls['syscall'].unique().tolist())
    
    for df in dfs.values():
        df['syscall'] = pd.Categorical(df['syscall'], categories=unique_syscalls, ordered=True)

    fig, axs = plt.subplots(2, 4, figsize=(18, 10), sharex=True, sharey=True)
    for row, (label, _, _) in enumerate(datasets):
        for col, err in enumerate(error_types):
            ax = axs[row, col]
            df = dfs[(label, err)]
            scatter = sns.scatterplot(
                data=df,
                x='retval',
                y='syscall',
                hue='when',
                palette='viridis',
                legend=(row == 0 and col == len(error_types) - 1),
                ax=ax
            )
            if row == 0:
                ax.set_title(titles[col], fontsize=14)
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
    if handles:
        fig.legend(handles, labels, title='when', loc='upper right', bbox_to_anchor=(1.04, 0.95), fontsize=12, title_fontsize=13)

    fig.supxlabel('Return Value (log scale)', fontsize=15)
    plt.tight_layout()
    plt.show()


def plot_error_instances_no_changes(data1, data2):
    llm_config = "/home/jom8be/workspaces/data/config/gpt-4o"
    random_config = "/home/jom8be/workspaces/data/config_random_log/gpt-4o"

    result_types = ['no_changes']

    df1 = process_dataset(data1, llm_config, result_types)['no_changes']
    df2 = process_dataset(data2, random_config, result_types)['no_changes']

    # get unique syscalls
    all_syscalls = pd.concat([data1, data2])
    unique_syscalls = sorted(all_syscalls['syscall'].unique().tolist())

    for df in [df1, df2]:
        df['syscall'] = pd.Categorical(df['syscall'], categories=unique_syscalls, ordered=True)

    fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)

    for ax, df, title in zip(axs, [df1, df2], ['SyscaLLM (GPT-4o)', 'Random']):
        sns.scatterplot(
            data=df,
            x='retval',
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
        ax.get_legend().remove()

    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, title='when', loc='upper left', bbox_to_anchor=(0.9, 0.95))
    fig.supxlabel('Return Value for No Changes (log scale)', fontsize=14)
    plt.tight_layout(pad=1.0, w_pad=0.5, h_pad=0.5, rect=[0, 0, 0.9, 1])
    plt.show()


def main():    
    # initialize accumulators as empty Series
    all_llm_data = pd.DataFrame() 
    all_random_data = pd.DataFrame()

    for i in range(1, runs + 1):
        # file paths
        llm_generated_file = f'/home/jom8be/workspaces/data/result/result{i}.csv'
        random_generated_file = f'/home/jom8be/workspaces/data/result/result_random_log{i}.csv'

        # read data
        llm_data, random_data = read_data(llm_generated_file, random_generated_file)

        # drop 'timeout' column
        llm_data = llm_data.drop(columns=['timeout'])
        random_data = random_data.drop(columns=['timeout'])

        # add run column
        llm_data = add_run_column(llm_data, i)
        random_data = add_run_column(random_data, i)
        
        # add syscall column
        llm_data = add_syscall_column(llm_data)
        random_data = add_syscall_column(random_data)

        # accumulate all data
        all_llm_data = pd.concat([all_llm_data, llm_data], ignore_index=True)
        all_random_data = pd.concat([all_random_data, random_data], ignore_index=True)

    # Reorder columns for better readability
    column_order = ['id', 'syscall', 'run'] + outcome_types
    all_llm_data = all_llm_data[column_order]
    all_random_data = all_random_data[column_order]
    
    print_statistics(all_llm_data, all_random_data)
    print_silent_data_corruption_syscalls(all_llm_data, all_random_data)

    plot_test_case_distribution(all_llm_data)

    # plot outcome rates for SyscaLLM (GPT-4o) and Random
    plot_outcome(all_llm_data, all_random_data)
    
    # plot normalized failure types by syscall
    plot_outcome_per_syscall(all_llm_data, all_random_data)

    # plot failure types by syscall
    plot_failure_per_syscall(all_llm_data, all_random_data)

    # plot silent data corruption by syscall
    plot_silent_data_corruption_by_syscall(all_llm_data, all_random_data)

    plot_error_instances(all_llm_data, all_random_data)
    plot_error_instances_no_changes(all_llm_data, all_random_data)

if __name__ == "__main__":
    main()
