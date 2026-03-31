# SyscaLLM: COTS App-Level Safety Testing Tool

SyscaLLM is an [system call](https://en.wikipedia.org/wiki/System_call) error injection testing framework that combines Large Language Models (LLMs) with error injection techniques to monitor software robustness. It provides a comprehensive testbed for evaluating application robustness by emulating a wide range of operating system error conditions via system call manipulation using [strace](https://man7.org/linux/man-pages/man1/strace.1.html).

## Overview

The general workflow of SyscaLLM is as follows:

```
Manual Pages → LLM Generation → JSON Tests → Strace Commands → Configurations → Error Injection → Analysis
```

SyscaLLM is structured around four main components, each aligned with key stages of this workflow:

1. **LLM-based System Call Test Generation** (`syscallm-generation/`): Covers the `Manual Pages → LLM Generation → JSON Tests` stages. This module uses LLMs to generate system call error injection tests based on Linux man pages. This is added as a subdirectory [syscallm-generation](https://github.com/boschresearch/syscallm-generation/tree/main).
2. **Errorload Processing Pipeline** (`src/process-json/`): Implements the `JSON Tests → Strace Commands → Configurations` stages. It processes the LLM-generated JSON tests into executable error injection configurations that can be used in the error injection environment.
3. **Error Injection Testbed** (`syscallm-injection/`): Corresponds to the `Error Injection` stage. This Docker-based testbed simulates faulty Linux OS behavior by injecting system call errors. This is added as a subdirectory [syscallm-injection](https://github.com/boschresearch/syscallm-injection/tree/main).
4. **Visualization of Experiment Results** (`src/plot/`): Supports the `Analysis` stage. This component provides scripts and tools to visualize and interpret application behavior in response to injected system call errors.

## Features

- **Automated Test Generation**: Uses GPT-5.2 to generate realistic system call failure scenarios
- **Comprehensive Error Injection**: Supports both success return value and error code for system calls manipulation
- **Real-world Application Testing**: Pre-configured support for Redis, memcached, Python, Nginx and other applications
- **Configurable Error Distribution**: Supports uniform and logarithmic error distribution patterns
- **Error Injection Environment**: Isolated Docker-based testing with system call monitoring
- **Detailed Analysis Tools**: Visualization and analysis scripts for test results and coverage

## Installation

First, clone this repository and its subrepository (submodule):

```bash
# clone the main repository
git clone https://github.com/boschresearch/syscallm.git
cd syscallm

# initialize and update submodules
git submodule update --init --recursive
```

## Quick Start

1. Install dependencies for `syscallm-generation`
``` bash
pip install -r syscallm-generation/requirements.txt
```
2. [Set up the environment](https://github.com/boschresearch/syscallm-injection/wiki/2.-Setup) for `syscallm-injection`
3. Extract Linux manual pages
``` bash
cd ./syscallm-generation
bash ./scripts/extract_syscall_man_pages.sh
```
4. Generate JSON files with LLM
``` bash
bsub < gpt5.2.bsub
```
5. Configure environment variables
``` bash
cd ../syscallm-injection
source ./config/configure
```
6. Process JSON files to strace command options
``` bash
bash ../scripts/process_json.sh
```
7. Build the syscall monitor image
``` bash
bash ./scripts/build_monitor_image.sh
```
8. Build wrapped application image
``` bash
bash ./scripts/build_test_image.sh
```
9. Run injection
``` bash
bash ./scripts/batch.sh
```

## How it Works

SyscaLLM orchestrates a multi-stage workflow to test application robustness against OS-level errors by injecting errors into system calls. Here, we break down each stage of this pipeline:

### 1. Automated Test Generation

The LLM generates test cases based on the following components:

- **Prompt** (`syscallm-generation/src/prompt.py`): Guides the LLM to generate erroneous values for system call success return values and error codes. The current prompt is targeting **valid return value errors** (i.e., return values that fall within a valid range but are incrrect in context) and **invalid return value errors** (i.e., clearly invalid values, such as numbers that exceed the data type range or violate syscall specifications)
- **Manual Pages** (`syscallm-generation/scripts/extract_syscall_man_pages.sh`): Serves as prior knowledge for each system call and dynamically inserted into the prompt.
- **JSON Schema** (`syscallm-generation/src/output_json_schema.py`): Defines the expected structure of the LLM-generated test cases, which improves the quality of the output. See [JSON schema](https://github.com/boschresearch/syscallm-generation/blob/main/src/output_json_schema.py).

To understand the details of LLM-based test generation, see [`syscallm-generation/README.md`](https://github.com/boschresearch/syscallm-generation) for information on:

- How to extract manual pages for each system call
- Setting up `OPENAI_ENDPOINT` and `OPENAI_API_KEY` and configuring model parameters

A sample LLM-generated test case for the *accept4* system call's success return values:

``` json
{
  "test_values": [
    0,
    1,
    2,
    1024,
    65536,
    2147483647,
    4294967295,
    9223372036854775807,
    18446744073709551615
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
    - Converts the strace command to the specific config file format that `syscallm-injection` uses for error injection. 
6. **Sampling**
    - There could be extensive amount of config files generated for one application-under-test. Therefore, we sample config files randomly for each run.
7. **Generating random config files**
    - Produces a separate set of random configurations to serve as a baseline in the associated scientific publication.

A sample of one config files related to the system call *accept4*, after the pipeline:

``` json
{
    "syslog_monitor_config": {
        "id": "accept4_98",
        "strace_output": "/export/strace.output.{id}",
        "output": [
            {
                "format": "csv",
                "target": "/export/output.{id}.csv"
            }
        ],
        "faults": [
            "inject=accept4:retval=4294967295:when=14..14"
        ]
    }
}
```

### 3. Error Injection Testbed

First, make sure you have set up your test environment, specified in [Error Injection - Setup](https://github.com/boschresearch/syscallm-injection/wiki/2.-Setup). For a quick start, follow [Error Injection - Quick Start](https://github.com/boschresearch/syscallm-injection/wiki/3.-Usage#quick-start).

A very detailed documentation is provided in [`syscallm-injection/README.md`](https://github.com/boschresearch/syscallm-injection) that includes:

- How to configure the experiment environment
- How to test your own application
- How to build a monitor component
- How to build a test image
- How to run the experiments
- How to extract the experiment results

After running the experiments and extracting the results by:

```bash
python3 ./syscallm-injection/src/failure_analysis/main.py --output result.csv
```

### 4. Visualization of Experiment Results

Generate coverage and failure analysis plots by:

```bash
# analyze failure patterns
python3 src/plot/plot_failure.py
```

## Open Source Software
This project relies on the usage of open-source Python libraries. Please see [`syscallm-generation/README.md`](https://github.com/boschresearch/syscallm-generation) and [`syscallm-injection/README.md`](https://github.com/boschresearch/syscallm-injection).

## Contact

For any questions or issues, please contact [Min Hee Jo](mailto:MinHee.Jo@de.bosch.com).

## License

SyscaLLM is open-sourced under the AGPL-3.0 license. See the LICENSE file for details.
