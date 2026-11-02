# Python 3.11 Requirements Checker

A simple script that checks whether pinned package versions in a requirements file declare compatibility with Python 3.11.

## Setup

Create and activate the virtual environment:

```bash
python3 -m venv pypi_check_env
source pypi_check_env/bin/activate
```

Install the required dependencies:

```bash
pip install -r code_requirements.txt
```

## Usage

Run the script using the default `requirements.txt` file:

```bash
python check_requirements.py
```

Or specify a different requirements file:

```bash
python check_requirements.py my_requirements.txt
```

## Output

The script reports:

- Total number of dependencies checked.
- Packages or versions not found on PyPI.
- Packages incompatible with Python 3.11.
- Dependency with the highest minimum Python version requirement.

**Note:** The script checks Python compatibility using package metadata available on PyPI. It does not guarantee successful installation.