# Environment Setup

This folder contains everything needed to set up the Python virtual environment and runtime configuration.

## Contents

| File / Folder       | Purpose                                      |
|---------------------|----------------------------------------------|
| `requirements.txt`  | Python package dependencies                  |
| `setup_venv.bat`    | Create venv on Windows                       |
| `setup_venv.sh`     | Create venv on Linux / macOS                 |
| `.env.example`      | Template for environment variables           |
| `venv/`             | Virtual environment (created locally, not in git) |

## Quick Start (Windows)

```bat
cd djangoacadstat
environment\setup_venv.bat
environment\venv\Scripts\activate
pip install -r environment\requirements.txt
```

## Quick Start (Linux / macOS)

```bash
cd djangoacadstat
bash environment/setup_venv.sh
source environment/venv/bin/activate
pip install -r environment/requirements.txt
```

## Environment Variables

Copy `.env.example` to the project root as `.env` and fill in your values:

```bash
copy environment\.env.example .env        # Windows
cp environment/.env.example .env          # Linux / macOS
```
