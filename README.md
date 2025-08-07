# SyscaLLM: COTS App-Level Safety Testing Tool

SyscaLLM is an [system call](https://en.wikipedia.org/wiki/System_call) error injection testing framework that combines Large Language Models (LLMs) with error injection techniques to monitor software robustness. It provides a comprehensive testbed for evaluating application robustness by emulating a wide range of operating system error conditions via system call manipulation using [strace](https://man7.org/linux/man-pages/man1/strace.1.html).

For a high-level overview and additional context, please refer to the [Application Error Handling Testing documentation](https://inside-docupedia.bosch.com/confluence2/display/ICT174/Application+Error+Handling+Testing).

## Overview

The general workflow of SyscaLLM is as follows:

```
Manual Pages → LLM Generation → JSON Tests → Strace Commands → Configurations → Error Injection → Analysis
```

SyscaLLM is structured around four main components, each aligned with key stages of this workflow:

1. **LLM-based System Call Test Generation** (`llm-syscall/`): Covers the `Manual Pages → LLM Generation → JSON Tests` stages. This module uses LLMs to generate system call error injection tests based on Linux man pages. This is added as a subdirectory [llm-syscall](https://github.boschdevcloud.com/bios-SPARTA/llm-syscall/tree/main) and high-level overview is documented in [here](https://inside-docupedia.bosch.com/confluence2/display/ICT174/1.+LLM-Based+Error+Injection+Test+Generation).
2. **Errorload Processing Pipeline** (`src/process-json/`): Implements the `JSON Tests → Strace Commands → Configurations` stages. It processes the LLM-generated JSON tests into executable error injection configurations that can be used in the fuzzing environment.
3. **Safety Fuzzing Testbed** (`safety-fuzzing/`): Corresponds to the `Error Injection` stage. This Docker-based testbed simulates faulty Linux OS behavior by injecting system call errors. This is added as a subdirectory [safety-fuzzing](https://github.boschdevcloud.com/bios-SPARTA/safety-fuzzing/tree/main) and high-level overview is documented [here](https://inside-docupedia.bosch.com/confluence2/display/ICT174/2.+System+Call+Error+Injection).
4. **Visualization of Experiment Results** (`src/plot/`): Supports the `Analysis` stage. This component provides scripts and tools to visualize and interpret application behavior in response to injected system call errors.

## Features

- **Automated Test Generation**: Uses GPT-4o, Qwen models to generate realistic system call failure scenarios
- **Comprehensive Error Injection**: Supports both success return value and error code for system calls manipulation
- **Real-world Application Testing**: Pre-configured support for Redis, memcached, Python, Nginx and other applications
- **Configurable Error Distribution**: Supports uniform and logarithmic error distribution patterns
- **Safety Fuzzing Environment**: Isolated Docker-based testing with system call monitoring
- **Detailed Analysis Tools**: Visualization and analysis scripts for test results and coverage

## Installation

First, clone this repository and its subrepository (submodule):

```bash
# clone the main repository
git clone https://github.boschdevcloud.com/bios-SPARTA/syscallm
cd syscallm

# initialize and update submodules
git submodule update --init --recursive
```

## Quick Start

1. Install dependencies for `llm-syscall`
``` bash
pip install -r llm-syscall/requirements.txt
```
2. [Set up the environment](https://github.boschdevcloud.com/bios-SPARTA/safety-fuzzing/wiki/Setup) for `safety-fuzzing`
3. One script for the whole workflow.
``` bash
bash scripts/run.sh
```

## How it Works

SyscaLLM orchestrates a multi-stage workflow to test application robustness against OS-level errors by injecting errors into system calls. Here, we break down each stage of this pipeline:

### 1. Automated Test Generation

The LLM generates test cases based on the following components:

- **Prompt** (`llm-syscall/src/prompt.py`): Guides the LLM to generate erroneous values for system call success return values and error codes. The current prompt is targeting **valid return value errors** (i.e., return values that fall within a valid range but are incrrect in context) and **invalid return value errors** (i.e., clearly invalid values, such as numbers that exceed the data type range or violate syscall specifications)
- **Manual Pages** (`llm-syscall/scripts/extract_syscall_man_pages.sh`): Serves as prior knowledge for each system call and dynamically inserted into the prompt.
- **JSON Schema** (`llm-syscall/src/output_json_schema.py`): Defines the expected structure of the LLM-generated test cases, which improves the quality of the output. See [JSON schema](https://github.boschdevcloud.com/bios-SPARTA/llm-syscall/blob/main/src/output_json_schema.py).

To understand the details of LLM-based test generation, see [`llm-syscall/README.md`](https://github.boschdevcloud.com/bios-SPARTA/llm-syscall/tree/main) for information on:

- How to extract manual pages for each system call
- Setting up `OPENAI_API_KEY` and configuring model parameters

A sample LLM-generated test case for the *accept* system call's success return values:

``` json
{
  "test_values": [
    0,
    1,
    2,
    3,
    1023,
    65535,
    1048576,
    2147483647,
    4294967295,
    9223372036854775807
  ]
}
```

### 2. Errorload Processing Pipeline

Run the complete errorload processing pipeline:

```bash
bash ./scripts/process_json.sh
```

This script will run `src/process_json/main.py` for the following steps:
1. **Processing JSON files that have out of bound values**
    - For success return values, it will filter out values that are below `0` and over `18446744073709551615`.
    - For error_codes, it will filter out non-existing error codes (e.g., `EACCES`).
2. **Converting JSON files to strace commands**
    - Translates the filtered JSON test cases into corresponding strace tampering parameters.
3. **Filtering strace commands**
    - Uses `src/utils/app_syscalls.py` to identify system calls actually invoked by the application-under-test's error-free execution logs, and removes commands that are irrelevant for error injection.
4. **Adding when parameter to the strace commands**
    - For system calls that are invoked multiple times, error values to inject are propagated across every invocation.
5. **Convert strace command to error injection config files**
    - Converts the strace command to the specific config file format that `safety-fuzzing` uses for error injection. 
6. **Sampling**
    - There could be extensive amount of config files generated for one application-under-test. Therefore, we sample `1000` config files randomly for each run.
7. **Generating random config files**
    - Produces a separate set of random configurations to serve as a baseline in the associated scientific publication.

### 3. Safety Fuzzing Testbed

A very detailed documentation is provided in [`safety-fuzzing/README.md`](https://github.boschdevcloud.com/bios-SPARTA/safety-fuzzing/tree/main) that includes:

- How to configure the experiment environment
- How to build a monitor component
- How to build a test image
- How to run the experiments
- How to extract the experiment results

### 4. Visualization of Experiment Results

Generate coverage and failure analysis plots:

```bash
# analyze failure patterns
python3 src/plot_failure.py
```

## Open Source Software
This project relies on the usage of open-source Python libraries. Please see [`llm-syscall/README.md`](https://github.boschdevcloud.com/bios-SPARTA/llm-syscall/tree/main) and [`safety-fuzzing/README.md`](https://github.boschdevcloud.com/bios-SPARTA/safety-fuzzing/tree/main).

## Contact

For any questions or issues, please contact [JOM8BE](mailto:MinHee.Jo@de.bosch.com).

## License
License: BIOSL-v4

Copyright (c) 2009, 2018 Robert Bosch GmbH and its subsidiaries. This program and the accompanying materials are made available under the terms of the Bosch Internal Open Source License v4 which accompanies this distribution, and is available at http://bios.intranet.bosch.com/bioslv4.txt

