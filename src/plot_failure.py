import pandas as pd
import matplotlib.pyplot as plt

colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B']

def read_data(llm_file, random_file):
    # read data from CSV files
    llm_data = pd.read_csv(llm_file)
    random_data = pd.read_csv(random_file)
    return llm_data, random_data


def calculate_true_counts(data):
    # calculate true counts and percentages for each column
    true_counts = data.iloc[:, 1:].sum().astype(int)
    percentages = (true_counts / len(data) * 100).round(2)
    return true_counts, percentages


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
    plt.ylim(0, 740)
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

    plt.title('Failure Counts by Syscall', color='black', fontsize=14)
    plt.xlabel('Syscall', color='black', fontsize=12)
    plt.ylabel('Count', color='black', fontsize=12)
    plt.xticks(rotation=45, color='black')
    plt.yticks(color='black')
    plt.legend(facecolor='white', edgecolor='black', loc='upper left', ncol=1)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def main():
    # file paths
    llm_generated_file = '/home/jom8be/workspaces/llm-safety-fuzzing/data/result.csv'
    random_generated_file = '/home/jom8be/workspaces/llm-safety-fuzzing/data/result_random.csv'

    # read data
    llm_data, random_data = read_data(llm_generated_file, random_generated_file)

    # drop 'timeout' column
    llm_data = llm_data.drop(columns=['timeout'])
    random_data = random_data.drop(columns=['timeout'])

    # calculate true counts and percentages
    llm_true_counts, llm_percentages = calculate_true_counts(llm_data)
    random_true_counts, random_percentages = calculate_true_counts(random_data)

    # print results
    print("LLM-Generated")
    print(pd.DataFrame({'Count': llm_true_counts, 'Percentage': llm_percentages}))

    print("\nRandom-Generated")
    print(pd.DataFrame({'Count': random_true_counts, 'Percentage': random_percentages}))

    # add syscall column
    llm_data = add_syscall_column(llm_data)
    random_data = add_syscall_column(random_data)

    # get silent data corruption IDs and syscalls
    llm_silent_data_corruption_ids = get_silent_data_corruption_ids(llm_data)
    random_silent_data_corruption_ids = get_silent_data_corruption_ids(random_data)

    print("\nLLM-Generated: IDs with silent_data_corruption:")
    print(llm_silent_data_corruption_ids)

    print("\nRandom-Generated: IDs with silent_data_corruption:")
    print(random_silent_data_corruption_ids)

    llm_silent_data_corruption = get_silent_data_corruption_syscalls(llm_data)
    random_silent_data_corruption = get_silent_data_corruption_syscalls(random_data)

    print("\nLLM-Generated: syscalls with silent_data_corruption:")
    print(llm_silent_data_corruption)

    print("\nRandom-Generated: syscalls with silent_data_corruption:")
    print(random_silent_data_corruption)

    # plot failure types by syscall
    plot_failure_types_by_syscall(llm_data, 'Failure Types by Syscall (LLM-Generated)')
    plot_failure_types_by_syscall(random_data, 'Failure Types by Syscall (Random-Generated)')

    # plot silent data corruption by syscall
    plot_silent_data_corruption_by_syscall(llm_data, random_data)


if __name__ == "__main__":
    main()
