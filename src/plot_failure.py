import pandas as pd
import matplotlib.pyplot as plt
import config

plt.rcParams["font.family"] = "Times New Roman"

colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B']

# runs = config.runs
runs = 1

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
    true_counts = data[['app_crash', 'error_exit', 'app_hang', 'silent_data_corruption', 'no_changes']].sum().astype(int)
    percentages = (true_counts / len(data) * 100).round(2)
    return true_counts, percentages


def get_silent_data_corruption_ids(data):
    # get ids where silent_data_corruption is true
    return data[data['silent_data_corruption'] == True]['id'].tolist()


def get_silent_data_corruption_syscalls(data):
    # get unique syscalls where silent_data_corruption is true
    return set(data[data['silent_data_corruption'] == True]['syscall'].tolist())


def plot_normalized_failure_types_by_syscall(data, title):
    # plot normalized failure types grouped by syscall
    failure_types = [col for col in data.columns[1:-1] if col != "no_changes"]  # exclude 'id', 'syscall', and 'no_changes' columns
    failure_counts_by_syscall = data.groupby('syscall')[failure_types].sum()

    # Normalize the counts by dividing by the total counts per syscall
    normalized_failure_counts = failure_counts_by_syscall.div(failure_counts_by_syscall.sum(axis=1), axis=0)

    ax = normalized_failure_counts.plot(kind='bar', figsize=(8, 6), stacked=True, color=colors, edgecolor='black')

    plt.title(title, color='black', fontsize=14)
    plt.xlabel('Syscall', color='black', fontsize=12)
    plt.ylabel('Proportion', color='black', fontsize=12)
    plt.xticks(rotation=45, color='black')
    plt.yticks(color='black')
    plt.legend(title='Failure Type', facecolor='white', edgecolor='black', loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=4)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def plot_failure_types_by_syscall(data, title):
    # plot failure types grouped by syscall
    failure_types = [col for col in data.columns[1:-1] if col != "no_changes"]  # exclude 'id', 'syscall', and 'no_changes' columns
    failure_counts_by_syscall = data.groupby('syscall')[failure_types].sum()

    ax = failure_counts_by_syscall.plot(kind='bar', figsize=(8, 6), stacked=True, color=colors, edgecolor='black')

    plt.title(title, color='black', fontsize=14)
    plt.xlabel('Syscall', color='black', fontsize=12)
    plt.ylabel('Count', color='black', fontsize=12)
    plt.xticks(rotation=45, color='black')
    plt.yticks(color='black')
    # plt.ylim(0, 3000)
    plt.legend(title='Failure Type', facecolor='white', edgecolor='black', loc='upper left', ncol=1)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def plot_average_failure_types_by_syscall(datas, title):
    # calculate average failure types grouped by syscall
    failure_types = [col for col in datas[0].columns[1:-1] if col != "no_changes"]  # exclude 'id', 'syscall', and 'no_changes' columns
    failure_counts_by_syscall_list = [data.groupby('syscall')[failure_types].sum() for data in datas]

    # calculate the average failure counts across all data
    average_failure_counts_by_syscall = sum(failure_counts_by_syscall_list) / len(failure_counts_by_syscall_list)

    ax = average_failure_counts_by_syscall.plot(kind='bar', figsize=(8, 6), stacked=True, color=colors, edgecolor='black')

    plt.title(title, color='black', fontsize=14)
    plt.xlabel('Syscall', color='black', fontsize=12)
    plt.ylabel('Average Count', color='black', fontsize=12)
    plt.xticks(rotation=45, color='black')
    plt.yticks(color='black')
    # plt.ylim(0, 1000)
    plt.legend(title='Failure Type', facecolor='white', edgecolor='black', loc='upper left', ncol=1)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def plot_silent_data_corruption_by_syscall(llm_data, random_data):
    # plot silent data corruption counts grouped by syscall
    llm_syscall_counts = llm_data[llm_data['silent_data_corruption'] == True]['syscall'].value_counts()
    random_syscall_counts = random_data[random_data['silent_data_corruption'] == True]['syscall'].value_counts()

    failure_counts = pd.DataFrame({
        'LLM-Generated': llm_syscall_counts,
        'Random-Generated': random_syscall_counts
    }).fillna(0).astype(int)

    ax = failure_counts.plot(kind='bar', figsize=(6, 4), color=colors, edgecolor='black')

    plt.title('Syscalls resulted in Silent Data Corruption', color='black', fontsize=14)
    plt.xlabel('Syscall', color='black', fontsize=12)
    plt.ylabel('Count', color='black', fontsize=12)
    plt.xticks(rotation=45, color='black')
    plt.yticks(color='black')
    plt.legend(facecolor='white', edgecolor='black', loc='upper left', ncol=1)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
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
        
        # accumulate total count
        total_count.append(len(llm_data))

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

        llm_silent_data_corruption = get_silent_data_corruption_syscalls(llm_data)
        random_silent_data_corruption = get_silent_data_corruption_syscalls(random_data)

        print(f"\nLLM-Generated#{i} - syscalls with silent_data_corruption:")
        print(llm_silent_data_corruption)

        print(f"\nRandom-Generated#{i} - syscalls with silent_data_corruption:")
        print(random_silent_data_corruption)

    # calculate failure counts and percentages grouped by "run"
    llm_failure_counts = all_llm_data.groupby('run', group_keys=False).apply(
        lambda group: calculate_failure(group)[0],
        include_groups=False
    )
    llm_failure_percentages = all_llm_data.groupby('run', group_keys=False).apply(
        lambda group: calculate_failure(group)[1],
        include_groups=False
    )
    random_failure_counts = all_random_data.groupby('run', group_keys=False).apply(
        lambda group: calculate_failure(group)[0],
        include_groups=False
    )
    random_failure_percentages = all_random_data.groupby('run', group_keys=False).apply(
        lambda group: calculate_failure(group)[1],
        include_groups=False
    )

    # average count and percentage across runs
    avg_llm_failure_counts = llm_failure_counts.mean().round(2)
    avg_llm_failure_percentages = llm_failure_percentages.mean().round(2)
    avg_random_failure_counts = random_failure_counts.mean().round(2)
    avg_random_failure_percentages = random_failure_percentages.mean().round(2)

    print(f"\nTotal test counts for each run: {total_count}\n")    
    print(f"LLM-Generated (Average over {runs} runs)")
    print(pd.DataFrame({
        'Average Count': avg_llm_failure_counts,
        'Average %': avg_llm_failure_percentages
    }))

    print(f"\nRandom-Generated (Average over {runs} runs)")
    print(pd.DataFrame({
        'Average Count': avg_random_failure_counts,
        'Average %': avg_random_failure_percentages
    }))

    # # plot failure types by syscall
    # plot_failure_types_by_syscall(llm_data, 'Failure Types by Syscall (LLM-Generated)')
    # # plot_average_failure_types_by_syscall(random_datas, 'Failure Types by Syscall (Average Random-Generated)')

    # # plot normalized failure types by syscall
    # plot_normalized_failure_types_by_syscall(llm_data, 'Failure Types by Syscall (LLM-Generated)')
    # # plot_normalized_failure_types_by_syscall(random_datas[0], 'Failure Types by Syscall (Random-Generated)')

    # # TODO: Fair comparison
    # # plot silent data corruption by syscall
    # plot_silent_data_corruption_by_syscall(llm_data, random_datas[0])


if __name__ == "__main__":
    main()
