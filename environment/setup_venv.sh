#!/usr/bin/env bash
# Create the Python virtual environment (Linux / macOS)
cd "$(dirname "$0")"

if [ -d "venv" ]; then
    echo "Virtual environment already exists at environment/venv"
else
    python3 -m venv venv
    echo "Created virtual environment at environment/venv"
fi

echo ""
echo "Next steps:"
echo "  1. Activate:  source environment/venv/bin/activate"
echo "  2. Install:   pip install -r environment/requirements.txt"
echo "  3. Run app:   python manage.py runserver"
