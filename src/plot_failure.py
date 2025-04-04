import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Times New Roman"

colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B']

def read_data(llm_file, random_files):
    # read data from CSV files
    llm_data = pd.read_csv(llm_file)
    random_datas = []
    for random_file in random_files:
        # read each random file and concatenate to the llm_data
        random_data = pd.read_csv(random_file)
        random_datas.append(random_data)

    return llm_data, random_datas


def calculate_true_counts(data):
    # calculate true counts and percentages for each column
    true_counts = data.iloc[:, 1:].sum().astype(int)
    percentages = (true_counts / len(data) * 100).round(2)
    return true_counts, percentages


def calculate_average_true_counts(random_datas):
    # calculate average true counts and percentages across all random data
    total_true_counts = None
    total_percentages = None
    for random_data in random_datas:
        true_counts, percentages = calculate_true_counts(random_data)
        if total_true_counts is None:
            total_true_counts = true_counts
            total_percentages = percentages
        else:
            total_true_counts += true_counts
            total_percentages += percentages

    average_true_counts = (total_true_counts / len(random_datas)).round(2)
    average_percentages = (total_percentages / len(random_datas)).round(2)
    return average_true_counts, average_percentages


def add_syscall_column(data):
    # add a 'syscall' column based on the 'id' column
    data['syscall'] = data['id'].apply(lambda x: x.split('_')[0])
    return data


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
    plt.ylim(0, 3000)
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
    random_runs = 5

    # file paths
    llm_generated_file = '/home/jom8be/workspaces/llm-safety-fuzzing/data/test_result/result.csv'
    random_generated_files = [
        f'/home/jom8be/workspaces/llm-safety-fuzzing/data/test_result/result_random{i}.csv'
        for i in range(1, random_runs + 1)
    ]

    # read data
    llm_data, random_datas = read_data(llm_generated_file, random_generated_files)

    # drop 'timeout' column
    llm_data = llm_data.drop(columns=['timeout'])
    random_datas = [random_data.drop(columns=['timeout']) for random_data in random_datas]

    # calculate true counts and percentages
    llm_true_counts, llm_percentages = calculate_true_counts(llm_data)
    average_random_true_counts, average_random_percentages = calculate_average_true_counts(random_datas)

    # print results
    print("LLM-Generated")
    print(pd.DataFrame({'Count': llm_true_counts, 'Percentage': llm_percentages}))

    print("\nRandom-Generated (Average)")
    print(pd.DataFrame({'Count': average_random_true_counts, 'Percentage': average_random_percentages}))

    # add syscall column
    llm_data = add_syscall_column(llm_data)
    random_datas = [add_syscall_column(random_data) for random_data in random_datas]

    # get silent data corruption IDs and syscalls
    llm_silent_data_corruption_ids = get_silent_data_corruption_ids(llm_data)
    random_silent_data_corruption_ids = [get_silent_data_corruption_ids(random_data) for random_data in random_datas]

    print("\nLLM-Generated: IDs with silent_data_corruption:")
    print(llm_silent_data_corruption_ids)

    for i, random_ids in enumerate(random_silent_data_corruption_ids):
        print(f"\nRandom-Generated {i + 1}: IDs with silent_data_corruption:")
        print(random_ids)

    llm_silent_data_corruption = get_silent_data_corruption_syscalls(llm_data)
    random_silent_data_corruptions = [get_silent_data_corruption_syscalls(random_data) for random_data in random_datas]

    print("\nLLM-Generated: syscalls with silent_data_corruption:")
    print(llm_silent_data_corruption)

    for i, random_silent_data_corruption in enumerate(random_silent_data_corruptions):
        print(f"\nRandom-Generated {i + 1}: syscalls with silent_data_corruption:")
        print(random_silent_data_corruption)

    # TODO: Fair comparison
    # plot failure types by syscall
    plot_failure_types_by_syscall(llm_data, 'Failure Types by Syscall (LLM-Generated)')
    plot_failure_types_by_syscall(random_datas[0], 'Failure Types by Syscall (Random-Generated)')

    # plot normalized failure types by syscall
    plot_normalized_failure_types_by_syscall(llm_data, 'Failure Types by Syscall (LLM-Generated)')
    plot_normalized_failure_types_by_syscall(random_datas[0], 'Failure Types by Syscall (Random-Generated)')

    # # plot silent data corruption by syscall
    plot_silent_data_corruption_by_syscall(llm_data, random_datas[0])


if __name__ == "__main__":
    main()
