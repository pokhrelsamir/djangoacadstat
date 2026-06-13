# Scripts

Utility scripts for setup, debugging, and maintenance. These are **not** part of the Django runtime.

## Contents

| Folder    | Purpose                                      |
|-----------|----------------------------------------------|
| `setup/`  | One-off setup scripts (e.g. populate teachers) |
| `debug/`  | Development and debugging utilities          |
| `patches/`| One-off code patch scripts                   |

## Running a script

Activate the virtual environment first, then run from the project root:

```bash
environment\venv\Scripts\activate
python scripts/setup/populate_teachers.py
```
