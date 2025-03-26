import pandas as pd

# file paths
llm_generated_file = '/home/jom8be/workspaces/llm-safety-fuzzing/data/result.csv'
random_generated_file = '/home/jom8be/workspaces/llm-safety-fuzzing/data/result_random.csv'

# read the CSV files into pandas DataFrames
llm_data = pd.read_csv(llm_generated_file)
random_data = pd.read_csv(random_generated_file)

# count the sum of True values for each column (excluding the 'id' column)
llm_true_counts = llm_data.iloc[:, 1:].sum().astype(int)
random_true_counts = random_data.iloc[:, 1:].sum().astype(int)

# print the results
print("LLM-Generated Data True Counts:")
print(llm_true_counts)

print("\nRandom-Generated Data True Counts:")
print(random_true_counts)

