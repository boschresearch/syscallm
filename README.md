# SyscaLLM

SyscaLLM is an system call fault injection testing framework that combines Large Language Models (LLMs) with error injection techniques to monitor software robustness and reliability. The project automates the generation of system call error injection test cases and provides a comprehensive testbed for evaluating application behavior under various fault conditions.

## Overview

SyscaLLM consists of three main components:

1. **LLM-based System Call Test Generation** (`llm-syscall/`): Leverages LLMs to generate system call error injection tests based on manual pages
2. **Safety Fuzzing Testbed** (`safety-fuzzing/`): A Docker-based fuzzing environment that simulates faulty Linux OS behavior
3. **Fault Load Processing Pipeline** (`src/`): Processes LLM-generated tests into executable fault injection configurations

## Features

- **Automated Test Generation**: Uses GPT-4o, Qwen, and other LLMs to generate realistic system call failure scenarios
- **Comprehensive Fault Injection**: Supports both error code injection and success value manipulation
- **Real-world Application Testing**: Pre-configured support for Redis, memcached, Python, Nginx and other applications
- **Configurable Fault Distribution**: Supports uniform and logarithmic fault distribution patterns
- **Safety Fuzzing Environment**: Isolated Docker-based testing with system call monitoring
- **Detailed Analysis Tools**: Visualization and analysis scripts for test results and coverage

## Installation

First, clone this repository and its subrepository (submodule):

```bash
# Clone the main repository
git clone https://github.boschdevcloud.com/bios-SPARTA/syscallm
cd syscallm

# Initialize and update submodules
git submodule update --init --recursive
```

## Workflow

```
Manual Pages → LLM Generation → JSON Tests → Strace Commands → Configurations → Error Injection → Analysis
```

## Quick Start

### Basic Usage

The basic usage of SyscaLLM is compiled in `scripts/run.sh`, which includes the following steps (1 to 3):

#### 1. Generate Test Cases with LLMs

To understand the details of LLM-based test generation, see [`llm-syscall/README.md`](llm-syscall/README.md) for information on:

- How to extract manual pages for each system call
- Setting up `OPENAI_API_KEY` and configuring model parameters
- Customizing prompt templates and test generation settings
- Generating JSON-formatted lists of error injection test values for each system call

#### 2. Process LLM Generated Tests into Fault Configurations

Run the complete fault load processing pipeline:

```bash
bash ./scripts/process_json.sh
```

#### 3. Run Safety Fuzzing Tests

To understand the details of error injections, see [`safety-fuzzing/README.md`](safety-fuzzing/README.md) for information on:

- How to configure the experiment environment
- How to build a monitor component
- How to build a test image
- How to run the experiments
- How to extract the experiment results

#### 4. Plotting the Error Injection Results

Generate coverage and failure analysis plots:

```bash
cd src

# Plot system call coverage
python3 plot_coverage.py

# Analyze failure patterns
python3 plot_failure.py

# Generate adaptability metrics
python3 plot_adaptability.py
```

## Open Source Software
This project relies on the usage of open-source Python libraries. Please see [`llm-syscall/README.md`](llm-syscall/README.md) and [`safety-fuzzing/README.md`](safety-fuzzing/README.md).

## Contact

For any questions or issues, please contact [JOM8BE](mailto:MinHee.Jo@de.bosch.com).

## License
License: BIOSL-v4

Copyright (c) 2009, 2018 Robert Bosch GmbH and its subsidiaries. This program and the accompanying materials are made available under the terms of the Bosch Internal Open Source License v4 which accompanies this distribution, and is available at http://bios.intranet.bosch.com/bioslv4.txt

