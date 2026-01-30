# Project Name

> Short description of what this project does.

## Contents
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Setup (uv)](#setup-uv)
- [Common commands](#common-commands)

## Requirements
- **Git**
- **Python** version pinned in [`.python-version`](./.python-version)
- **uv** (dependency + environment management)

## Quick start
```bash
git clone <REPO_URL>
cd <REPO_FOLDER>

# Install uv (see below), ensure Python matches .python-version, then:
uv sync
uv run python -m <your_module>
```

## Setup (uv)

This project uses:
- **`pyproject.toml`** for project metadata and dependency declarations
- **`uv.lock`** for reproducible, pinned dependency versions
- **`.python-version`** to pin the Python version used for development

### 1) Install uv

**macOS / Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify:
```bash
uv --version
```

### 2) Install the correct Python version

This project uses [**Python 3.13**](./.python-version). If you run into any problems, check if you have installed and are using the correct python version using 
```bash
python --version
```


### 3) Create/sync the environment and install dependencies

From the repository root:

```bash
uv sync
```

This will create/update a local virtual environment (typically `.venv/`) and install the **exact** dependency versions from `uv.lock`.

## Common commands

> Replace placeholders like `<your_module>` with your project’s actual entry point.

Run Python:
```bash
uv run python -m <your_module>
```
