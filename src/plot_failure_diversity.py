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

# calculate the percentage of True values for each column
llm_percentages = (llm_true_counts / len(llm_data) * 100).round(2)
random_percentages = (random_true_counts / len(random_data) * 100).round(2)

# print the results
print("LLM-Generated")
print(pd.DataFrame({'Count': llm_true_counts, 'Percentage': llm_percentages}))

print("\nRandom-Generated")
print(pd.DataFrame({'Count': random_true_counts, 'Percentage': random_percentages}))

