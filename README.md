# AcadStat — Academic Statistics System

Django-based academic management system for student performance, attendance, exams, and reporting.

## Project Folder Structure


djangoacadstat/
│
├── environment/              
│   ├── requirements.txt
│   ├── setup_venv.bat       
│   ├── setup_venv.sh        
│   ├── .env.example
│   └── venv/                 
│
├── academicsys/              
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── core/                     
│   ├── models.py, views.py, forms.py, urls.py
│   ├── migrations/
│   ├── management/commands/
│   ├── templates/
│   └── static/
│
├── static/                   
├── media/                   
│
├── data/                    
│   └── backups/
│
├── samples/                  
│   └── bulk_marks_upload/
│
├── scripts/                  
│   ├── setup/                
│   ├── debug/               
│   └── patches/              
│
├── docs/                     
│   ├── Workflow.md
│   └── commands/
│
├── manage.py                 
└── README.md                 

