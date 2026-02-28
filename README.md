# Evolving Graph Structured Programs for Circuit Generation with Large Language Models

This repository contains the official implementation of our manuscript *Evolving Graph Structured Programs for Circuit Generation with Large Language Models*.

## Installation

### ABC Installation

We provide a precompiled `abc` executable for Linux as a compressed archive in the GitHub Releases of this repository. Download the archive from the Releases page and extract the `abc` binary into the root directory of this project. Due to potential compatibility issues across different operating systems and hardware platforms, users on non-Linux platforms are advised to compile the source code manually. For detailed compilation instructions and the official source code, please refer to the upstream repository: [berkeley-abc/abc](https://github.com/berkeley-abc/abc).

For details on how `abc` is used in this work, please refer to our [paper](https://openreview.net/pdf?id=DUtS9K9HH6).

### Python Environment

This project has **no strict Python version requirements**. `Python 3.12` is used in our environments. The key packages and their exact versions used during development and testing are listed below:

| Package | Version |
|---------|---------|
| `torch` | `2.10.0` |
| `numpy` | `2.4.2` |
| `tensorboard` | `2.20.0` |
| `boolean.py` | `5.0` |
| `requests` | `2.32.5` |
| `joblib` | `1.5.3` |

The complete list of dependencies is provided in `requirements.txt`. Install all required packages via:

```bash
pip install -r requirements.txt
```

## Running the Project

### Prerequisites

Before running the project, ensure the following conditions are met:

1. **ABC Executable**: Ensure the `abc` executable is present in the project's root directory and is runnable. For non-Linux platforms, compile it from [berkeley-abc/abc](https://github.com/berkeley-abc/abc).
2. **LLM Credentials**: Configure your LLM API credentials in `runEoh4AIG.py`:
   - Set `llm_api_endpoint` to your LLM API endpoint.
   - Set `llm_api_key` to your valid API key.
3. **Python Dependencies**: Install all required packages as described in the [Python Environment](#python-environment) section.

### Quick Start

Run the core script with the following sample configuration:

```bash
python runEoh4AIG.py \
  --truth_file_path ./example/circuit.truth \
  --ec_pop_size 10 \
  --ec_n_pop 10 \
  --llm_model gpt-3.5-turbo \
  --ec_operators e1 e2 m1 m2 \
  --sample_num 1000 \
  --local_search
```

### Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--truth_file_path` | `str` | `./example/circuit.truth` | Path to the input truth table file. |
| `--ec_pop_size` | `int` | `3` | Number of individuals in each evolutionary population. |
| `--ec_n_pop` | `int` | `5` | Number of evolutionary populations (generations). |
| `--ec_operators` | `list` | `['e1', 'm1']` | EOH operators to apply (supports `e1`, `e2`, `m1`, `m2`). |
| `--llm_model` | `str` | `gpt-3.5-turbo` | LLM model identifier (e.g., `gpt-4o`, `gpt-3.5-turbo`). |
| `--use_fx` | `flag` | `False` | Enable FX optimization. |
| `--local_search` | `flag` | `False` | Enable local search optimization. |
| `--random_generated` | `flag` | `False` | Generate random initial programs. |
| `--shannon_decomposition` | `flag` | `False` | Apply Shannon decomposition to the AIG. |
| `--LLM_generation_initial` | `flag` | `False` | Use LLM to generate the initial AIG programs. |
| `--legalized_parent` | `flag` | `False` | Use legalized parent prompts during generation. |

> For the full list of available parameters, refer to `runEoh4AIG.py`.

### Output

All experiment results — including the optimal AIG program and TensorBoard logs — are saved to a timestamped subdirectory under `./outputs/`.

### Additional Benchmarks

The repository includes a minimal example circuit in `./example/circuit.truth` for quick testing. For more comprehensive experimentation, we provide a collection of benchmark circuits from IWLS in our releases page:

- Download `benchmark.tar.gz` from the releases page
- Extract to the project root directory:
  ```bash
  tar -xzf benchmark.tar.gz
  ```
- Use benchmark circuits by updating `--truth_file_path` (e.g., `./benchmark/iwls2024/all/ex29.truth`)
