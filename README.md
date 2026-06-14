# AcadStat — Student Result and Performance Analysis System

Django-based academic management system for student performance,analysis and result generation.

## Project Folder Structure

```
djangoacadstat/
│
├── environment/              # Python venv, dependencies, and env config
│   ├── requirements.txt
│   ├── setup_venv.bat        # Windows venv setup
│   ├── setup_venv.sh         # Linux/macOS venv setup
│   ├── .env.example
│   └── venv/                 # Virtual environment (local only, gitignored)
│
├── academicsys/              # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── core/                     # Main Django application
│   ├── models.py, views.py, forms.py, urls.py
│   ├── migrations/
│   ├── management/commands/
│   ├── templates/
│   └── static/
│
├── static/                   # Project-wide static assets (CSS, JS, images)
├── media/                    # User-uploaded files (student images, materials)
│
├── data/                     # Database backups and exported data
│   └── backups/
│
├── samples/                  # Sample files and upload templates
│   └── bulk_marks_upload/
│
├── scripts/                  # Utility and maintenance scripts
│   ├── setup/                # One-off setup scripts
│   ├── debug/                # Development/debug utilities
│   └── patches/              # One-off code patch scripts
│
├── docs/                     # Project documentation and command references
│   ├── Workflow.md
│   └── commands/
│
├── manage.py                 # Django management entry point
└── README.md                 # This file
```

## Quick Start

```bat
REM 1. Create and activate virtual environment
environment\setup_venv.bat
environment\venv\Scripts\activate

REM 2. Install dependencies
pip install -r environment\requirements.txt

REM 3. Run migrations and start server
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
