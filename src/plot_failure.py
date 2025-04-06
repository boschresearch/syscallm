import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import config

plt.rcParams["font.family"] = "Times New Roman"
colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B']
outcome_types = ['app_crash', 'app_hang', 'error_exit', 'silent_data_corruption', 'no_changes']

# runs = config.runs
runs = 2

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
    data['syscall'] = data['id'].apply(lambda x: x.split('_')[0])
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
    
    print(f"Total test counts for each run: {llm['run'].value_counts()}")    
    print(f"---------------------------------------------------------------")
    print(f"LLM-Generated")
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
        print(f"Unique syscalls with silent data corruption (LLM): {llm_silent_data_corruption}")
        print(f"Unique syscalls with silent data corruption (Random): {random_silent_data_corruption}")


def plot_normalized_outcome_by_syscall(data, title):
    df = data.groupby('syscall')[outcome_types].sum().div(runs).reset_index()

    df[outcome_types] = df[outcome_types].div(df[outcome_types].sum(axis=1), axis=0).mul(100)

    xtick_labels = {
        'app_crash': 'App Crash',
        'app_hang': 'App Hang',
        'error_exit': 'Error Exit',
        'silent_data_corruption': 'Silent Data Corruption',
        'no_changes': 'No Changes'
    }
    
    df.rename(columns=xtick_labels, inplace=True)

    ordered_columns = ['No Changes', 'App Crash', 'Error Exit', 'App Hang', 'Silent Data Corruption']

    df = df[['syscall'] + ordered_columns]

    df_pivoted = df.pivot_table(index='syscall')

    ax = df_pivoted.plot(kind='barh', stacked=True, figsize=(10, 6))

    plt.title(title, fontsize=16)
    plt.xlabel('Percentage (%)', fontsize=14)
    plt.ylabel(None)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()


def plot_outcome_by_syscall(data, title):
    df = data.groupby('syscall')[outcome_types].sum().div(runs).reset_index()

    xtick_labels = {
        'app_crash': 'App Crash',
        'app_hang': 'App Hang',
        'error_exit': 'Error Exit',
        'silent_data_corruption': 'Silent Data Corruption',
        'no_changes': 'No Changes'
    }
    
    df.rename(columns=xtick_labels, inplace=True)

    ordered_columns = ['No Changes', 'App Crash', 'Error Exit', 'App Hang', 'Silent Data Corruption']

    df = df[['syscall'] + ordered_columns]

    df_pivoted = df.pivot_table(index='syscall')

    ax = df_pivoted.plot(kind='barh', stacked=True, figsize=(10, 6))

    plt.title(title, fontsize=16)
    plt.xlabel('Count', fontsize=14)
    plt.ylabel(None)
    plt.xticks(rotation=45, fontsize=12, ticks=range(0, 3500, 100))
    plt.yticks(fontsize=12)
    plt.xlim(0, 3500)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def plot_silent_data_corruption_by_syscall(llm, random):
    llm_counts = llm[llm['silent_data_corruption'] == True]['syscall'].value_counts()
    random_counts = random[random['silent_data_corruption'] == True]['syscall'].value_counts()

    df = pd.DataFrame({
        'syscall': llm_counts.index.append(random_counts.index).unique(),
        'LLM': llm_counts,
        'Random': random_counts
    })

    df = df.melt(
        id_vars='syscall',
        value_vars=['LLM', 'Random'],
        var_name='type',
        value_name='count'
    )
    
    df['count'] = df['count'].fillna(0).astype(int)

    plt.figure(figsize=(6, 4))

    sns.barplot(
        data=df,
        x='syscall',
        y='count',
        hue='type',
        edgecolor='black'
    )

    plt.title(f'Silent Data Corruption by Syscall (Accumulated over run={runs})', fontsize=16)
    plt.xlabel(None)
    plt.ylabel('Count', fontsize=14)
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.show()


def plot_outcome(llm, random):
    total_count = llm['run'].value_counts()

    llm_counts = llm[outcome_types].groupby(llm['run']).sum().reset_index()
    random_counts = random[outcome_types].groupby(random['run']).sum().reset_index()

    llm_counts['type'] = 'LLM'
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
        linewidth=2 
    )

    plt.title(f'Injection Outcome (run={runs})', fontsize=16)
    plt.ylabel('Average Rate (%)', fontsize=14)
    plt.xlabel('Outcome', fontsize=14)
    plt.xticks(rotation=15, fontsize=12)
    plt.yticks(fontsize=12)
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.show()


def main():    
    # initialize accumulators as empty Series
    total_count = []
    all_llm_data = pd.DataFrame() 
    all_random_data = pd.DataFrame()

    for i in range(1, runs + 1):
        # file paths
        llm_generated_file = f'/home/jom8be/workspaces/llm-safety-fuzzing/data/test_result/result{i}.csv'
        random_generated_file = f'/home/jom8be/workspaces/llm-safety-fuzzing/data/test_result/result_random{i}.csv'

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
    
    print_statistics(all_llm_data, all_random_data)
    print_silent_data_corruption_syscalls(all_llm_data, all_random_data)

    # plot outcome rates for LLM and Random
    plot_outcome(all_llm_data, all_random_data)
    
    # plot silent data corruption by syscall
    plot_silent_data_corruption_by_syscall(all_llm_data, all_random_data)

    # plot failure types by syscall
    plot_outcome_by_syscall(all_llm_data, f'LLM-Generated\nInjection Outcomes by Syscall (Average over {runs} runs)')
    plot_outcome_by_syscall(all_llm_data, f'Random-Generated\nInjection Outcomes by Syscall (Average over {runs} runs)')

    plot_outcome_by_syscall(all_llm_data, f'LLM-Generated\nInjection Outcomes by Syscall (Average over {runs} runs)')
    plot_outcome_by_syscall(all_llm_data, f'Random-Generated\nInjection Outcomes by Syscall (Average over {runs} runs)')

    # plot normalized failure types by syscall
    plot_normalized_outcome_by_syscall(all_llm_data, f'LLM-Generated\nInjection Outcomes by Syscall (Average over {runs} runs, normalized)')
    plot_normalized_outcome_by_syscall(all_random_data, f'Random-Generated\nInjection Outcomes by Syscall (Average over {runs} runs, normalized)')

if __name__ == "__main__":
    main()
