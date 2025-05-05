import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import config
import json
from app_syscalls import get_app_syscalls

plt.rcParams["font.family"] = "Times New Roman"
colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B']
outcome_types = ['no_changes', 'app_crash', 'app_hang', 'error_exit', 'silent_data_corruption']
renamed_outcome_types = ['No Changes', 'App Crash', 'App Hang', 'Error Exit', 'Silent Data Corruption']

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
    print("Average Percentages:")
    print(avg_llm_percentages.to_frame().T)
    print(f"---------------------------------------------------------------")
    print(f"Random-Generated")
    print("Counts:")
    print(random_counts)
    print("Percentages:")
    print(random_percentages)
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
    df1 = data1.groupby('syscall')[outcome_types].sum().div(runs).reset_index()
    df2 = data2.groupby('syscall')[outcome_types].sum().div(runs).reset_index()
    
    df1['type'] = 'SyscaLLM (GPT-4o)'
    df2['type'] = 'Random'

    failure_columns = ['app_crash', 'app_hang', 'error_exit', 'silent_data_corruption']

    for df in [df1, df2]:
        df['failures'] = df[failure_columns].sum(axis=1)
        df['no_changes'] = df['no_changes'].fillna(0)
        df['total'] = df['no_changes'] + df['failures']
        df['failures'] = df['failures'].div(df['total']).mul(100).round(2)
        
    df = pd.concat([df1, df2], ignore_index=True)
    df = df[['syscall', 'type', 'failures']]
    
    syscall_order = sorted(df['syscall'].unique())
    df['syscall'] = pd.Categorical(df['syscall'], categories=syscall_order, ordered=True)

    g = sns.catplot(
        data=df,
        kind='point',            # or 'strip', 'box', 'bar', etc.
        x='failures',
        y='syscall',
        hue='type',
        dodge=True,
        markers=['o', 'x'],
        linestyles=['-', '--'],
        linewidth=1.5,
        height=6,
        aspect=0.7,
        palette={'SyscaLLM (GPT-4o)': '#6A5ACD', 'Random': '#FF8C00'}
    )

    g.set_axis_labels("Failure Rate (%)", None, fontsize=16)

    for ax in g.axes.flat:
        ax.set_ylabel("")
        ax.yaxis.label.set_visible(False)
        ax.grid(linestyle='--', alpha=0.5)

    # Legend styling
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
    df1 = data1.groupby('syscall')[['app_crash', 'app_hang', 'error_exit', 'silent_data_corruption']].sum().div(runs).reset_index()
    df2 = data2.groupby('syscall')[['app_crash', 'app_hang', 'error_exit', 'silent_data_corruption']].sum().div(runs).reset_index()

    df1['type'] = 'SyscaLLM (GPT-4o)'
    df2['type'] = 'Random'

    df = pd.concat([df1, df2], ignore_index=True)

    outcome_labels = {
        'app_crash': 'App Crash',
        'app_hang': 'App Hang',
        'error_exit': 'Error Exit',
        'silent_data_corruption': 'Silent Data Corruption'
    }
    df.rename(columns=outcome_labels, inplace=True)

    df = df.melt(
        id_vars=['syscall', 'type'],
        value_vars=list(outcome_labels.values()),
        var_name='outcome_type',
        value_name='count'
    )

    pivot_df = df.pivot_table(
        index=['syscall', 'type'],
        columns='outcome_type',
        values='count',
        fill_value=0
    ).reset_index()

    types = pivot_df['type'].unique()
    fig, axs = plt.subplots(1, len(types), figsize=(14, 6), sharex=True, sharey=True)

    for i, t in enumerate(types):
        sub_df = pivot_df[pivot_df['type'] == t].set_index('syscall').drop(columns='type')
        sub_df.plot(
            kind='barh',
            stacked=True,
            ax=axs[i],
            color=[palette[col] for col in sub_df.columns],
            legend=False
        )
        if i == len(types) - 1:
            axs[i].legend(title=None, loc='upper right')
        axs[i].set_title(t, fontsize=15)
        axs[i].set_ylabel(None)
        axs[i].grid(linestyle='--', alpha=0.7)
        axs[i].invert_yaxis()
    fig.supxlabel('Count', fontsize=15)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.show()


def plot_silent_data_corruption_by_syscall(llm, random):
    llm_counts = llm[llm['silent_data_corruption'] == True]['syscall'].value_counts()
    random_counts = random[random['silent_data_corruption'] == True]['syscall'].value_counts()

    df = pd.DataFrame({
        'syscall': pd.concat([llm_counts, random_counts]).index,
        'count': pd.concat([llm_counts, random_counts]).values,
        'type': ['SyscaLLM (GPT-4o)'] * len(llm_counts) + ['Random'] * len(random_counts)
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


def plot_outcome(llm, random):
    total_count = llm['run'].value_counts()

    llm_counts = llm[outcome_types].groupby(llm['run']).sum().reset_index()
    random_counts = random[outcome_types].groupby(random['run']).sum().reset_index()

    llm_counts['type'] = 'SyscaLLM (GPT-4o)'
    random_counts['type'] = 'Random'

    df = pd.concat([llm_counts, random_counts], ignore_index=True)

    df[outcome_types] = df[outcome_types].astype(float)

    # normalize the outcome columns by dividing by the total count for each run
    for run in range(1, runs + 1):
        total = total_count[run]
        df.loc[df['run'] == run, outcome_types] = df.loc[df['run'] == run, outcome_types].div(total).mul(100).astype(float)
    
    xtick_labels = {
        'app_crash': 'App Crash',
        'app_hang': 'App Hang',
        'error_exit': 'Error Exit',
        'silent_data_corruption': 'Silent Data Corruption',
        'no_changes': 'No Changes'
    }

    df = df.melt(
        id_vars=['run', 'type'],
        value_vars=outcome_types,
        var_name='outcome_type',
        value_name='rate'
    )

    df['outcome_type'] = df['outcome_type'].map(xtick_labels)

    plt.figure(figsize=(5, 4))

    sns.lineplot(
        data=df,
        x='outcome_type',
        y='rate',
        hue='type',
        style='type',
        markers=True,
        linewidth=2,
        palette={'SyscaLLM (GPT-4o)': '#6A5ACD', 'Random': '#FF8C00'}
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
    # data.drop(columns=['id'], inplace=True)

    df = data.groupby(['run', 'syscall']).sum().reset_index()

    df['total'] = df[['app_crash', 'error_exit', 'app_hang', 'silent_data_corruption', 'no_changes']].sum(axis=1)
    
    df.drop(columns=outcome_types, inplace=True)

    syscall_dict = get_app_syscalls()

    for index, row in df.iterrows():
        syscall = row['syscall']
        if syscall in syscall_dict:
            df.at[index, 'total'] = row['total']

    for syscall in syscall_dict.keys():
        if syscall not in df['syscall'].values:
            for run in range(1, runs + 1):
                new_row = pd.DataFrame([{'run': run, 'syscall': syscall, 'total': 0}])
                df = pd.concat([df, new_row], ignore_index=True)

    pivot_df = df.pivot(index='syscall', columns='run', values='total')
    pivot_df.fillna(0, inplace=True)
    pivot_df = pivot_df.iloc[::-1]

    ax = pivot_df.plot(
        kind='barh',
        figsize=(6, 8),
        color=['#6A5ACD', '#FF8C00', '#2E8B57', '#DC143C', '#3471eb'],
        logx=True,
        width=0.8
    )

    for label in ax.get_yticklabels():
        if label.get_text() in ['pread64', 'rseq']:
            label.set_fontstyle('italic')
            label.set_color('red')
            label.set_alpha(0.7)
            label.set_text(f"{label.get_text()} (X)")

    plt.xlabel('Count (log scale)', fontsize=15)
    plt.ylabel(None)
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.legend(title='Run', fontsize=15, loc='upper right', bbox_to_anchor=(1, 0.7))
    plt.grid(linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def plot_silent_data_corruption_error_instances(data1, data2):
    # config files for SyscaLLM (GPT-4o) and Random
    llm_config = "/home/jom8be/workspaces/data/config/gpt-4o"
    random_config = "/home/jom8be/workspaces/data/config_random/gpt-4o"

    # filter out only sdc
    df1 = data1[data1['silent_data_corruption'] == True].copy()
    df2 = data2[data2['silent_data_corruption'] == True].copy()

    df1['retval'] = None
    df2['retval'] = None

    # iterate over rows
    for index, row in df1.iterrows():
        # id
        syscall = row['id']
        # run number
        run = row['run']

        # config file path that resulted in sdc
        config_path = f"{llm_config}/run{run}/{syscall}.json"

        with open(config_path, 'r') as file:
            # load JSON data
            config_data = json.load(file)

            # strace parameter for tampering
            strace_param = config_data['syslog_monitor_config']['faults'][0]

            # extract return value
            retval_start = strace_param.find("retval=") + len("retval=")
            retval_end = strace_param.find(":", retval_start)
            retval = strace_param[retval_start:retval_end]

            # add retval to the dataframe
            df1.loc[index, 'retval'] = int(retval)
            
    df1['retval'] = df1['retval'].astype(int)

    # iterate over rows
    for index, row in df2.iterrows():
        # id
        syscall = row['id']
        # run number
        run = row['run']

        # config file path that resulted in sdc
        config_path = f"{random_config}/run{run}/{syscall}.json"

        with open(config_path, 'r') as file:
            # load JSON data
            config_data = json.load(file)

            # strace parameter for tampering
            strace_param = config_data['syslog_monitor_config']['faults'][0]

            # extract return value
            retval_start = strace_param.find("retval=") + len("retval=")
            retval_end = strace_param.find(":", retval_start)
            retval = strace_param[retval_start:retval_end]

            # add retval to the dataframe
            df2.at[index, 'retval'] = int(retval)

    min_retval = df1['retval'].min()
    max_retval = df1['retval'].max()
    print(f"Minimum retval: {min_retval}, Maximum retval: {max_retval}")

    sns.relplot(
        data=df1,
        x='syscall',
        y='retval',
        hue='syscall',
        palette='viridis',
        legend=False
    )
    plt.xlabel('Syscall', fontsize=14)
    plt.ylabel('Return Value', fontsize=14)
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.yscale('log')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def main():    
    # initialize accumulators as empty Series
    all_llm_data = pd.DataFrame() 
    all_random_data = pd.DataFrame()

    for i in range(1, runs + 1):
        # file paths
        llm_generated_file = f'/home/jom8be/workspaces/data/result/result{i}.csv'
        random_generated_file = f'/home/jom8be/workspaces/data/result/result_random{i}.csv'

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
    # plot_outcome(all_llm_data, all_random_data)
    
    # # plot normalized failure types by syscall
    # plot_outcome_per_syscall(all_llm_data, all_random_data)

    # # plot failure types by syscall
    # plot_failure_per_syscall(all_llm_data, all_random_data)

    # # plot silent data corruption by syscall
    # plot_silent_data_corruption_by_syscall(all_llm_data, all_random_data)

    # plot_silent_data_corruption_error_instances(all_llm_data, all_random_data)

if __name__ == "__main__":
    main()
