import pandas as pd
import matplotlib.pyplot as plt

# file paths
llm_generated_file = '/home/jom8be/workspaces/llm-safety-fuzzing/data/result.csv'
random_generated_file = '/home/jom8be/workspaces/llm-safety-fuzzing/data/result_random.csv'

# read the CSV files into pandas DataFrames
llm_data = pd.read_csv(llm_generated_file)
random_data = pd.read_csv(random_generated_file)

# count the sum of True values for each column (excluding the 'id' column)
llm_true_counts = llm_data.iloc[:, 1:].sum().astype(int)
random_true_counts = random_data.iloc[:, 1:].sum().astype(int)

# calculate the percentage of True values for each column
llm_percentages = (llm_true_counts / len(llm_data) * 100).round(2)
random_percentages = (random_true_counts / len(random_data) * 100).round(2)

# print the results
print("LLM-Generated")
print(pd.DataFrame({'Count': llm_true_counts, 'Percentage': llm_percentages}))

print("\nRandom-Generated")
print(pd.DataFrame({'Count': random_true_counts, 'Percentage': random_percentages}))

# add a new column "syscall" to both datasets
llm_data['syscall'] = llm_data['id'].apply(lambda x: x.split('_')[0])
random_data['syscall'] = random_data['id'].apply(lambda x: x.split('_')[0])

# find and print the IDs that resulted in silent_data_corruption for each dataset
llm_silent_data_corruption_ids = llm_data[llm_data['silent_data_corruption'] == True]['id'].tolist()
random_silent_data_corruption_ids = random_data[random_data['silent_data_corruption'] == True]['id'].tolist()

print("\nLLM-Generated: IDs with silent_data_corruption:")
print(llm_silent_data_corruption_ids)

print("\nRandom-Generated: IDs with silent_data_corruption:")
print(random_silent_data_corruption_ids)

llm_silent_data_corruption = set(llm_data[llm_data['silent_data_corruption'] == True]['syscall'].tolist())
random_silent_data_corruption = set(random_data[random_data['silent_data_corruption'] == True]['syscall'].tolist())

print("\nLLM-Generated: syscalls with silent_data_corruption:")
print(llm_silent_data_corruption)

print("\nRandom-Generated: syscalls with silent_data_corruption:")
print(random_silent_data_corruption)

# count the occurrences of each syscall for failures in both datasets
llm_syscall_counts = llm_data[llm_data['silent_data_corruption'] == True]['syscall'].value_counts()
random_syscall_counts = random_data[random_data['silent_data_corruption'] == True]['syscall'].value_counts()

# create a DataFrame for plotting
failure_counts = pd.DataFrame({
    'LLM-Generated': llm_syscall_counts,
    'Random-Generated': random_syscall_counts
}).fillna(0).astype(int)

# plot the data
failure_counts.plot(kind='bar', figsize=(10, 6))
plt.title('Failure Counts by Syscall')
plt.xlabel('Syscall')
plt.ylabel('Count')
plt.xticks(rotation=45)
plt.legend(title='Dataset')
plt.tight_layout()
plt.show()