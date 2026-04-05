
# For workflow hover to the file named **Workflow.md**
 # Django Academic Statistics System

A comprehensive academic management system built with Django for managing student marks, attendance, QR code-based attendance tracking, and AI-powered student analysis.

## Features

- **User Authentication** - Login/Logout system with role-based access
- **Dashboard** - Central hub for all academic operations
- **Marks Management** - Add, view, and manage student marks
- **Mark Sheet Generation** - Generate individual student mark sheets
- **Student Analysis** - AI-powered analysis of student performance
- **QR Code System** - Generate and scan QR codes for attendance
- **Attendance Tracking** - Track and report student attendance
- **Admin Panel** - Full Django admin for data management

## Page Navigation Flow

### Entry Point
```
Home Page (/)
    │
    ├──────► Login (/login/)
    │
    └──────► Admin (/admin/)
```

### After Authentication
```
Dashboard (/dashboard/)
    │
    ├──────► Add Marks (/add-marks/)
    ├──────► Marks List (/marks-list/)
    ├──────► Mark Sheet (/mark-sheet/)
    ├──────► Student Analysis (/student-analysis/)
    ├──────► QR Codes (/qr-codes/)
    ├──────► QR Scanner (/qr-scanner/)
    ├──────► Attendance (/attendance/)
    ├──────► Attendance Report (/attendance-report/)
    └──────► Admin Panel (/admin/)
```

### Complete Navigation Diagram

```
                    ┌─────────────┐
                    │   Home (/)  │
                    └──────┬──────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
       ┌────▼─────┐                  ┌────▼─────┐
       │  Login   │                  │  Admin   │
       │ /login/  │                  │ /admin/  │
       └────┬─────┘                  └──────────┘
            │
            │ (authenticated)
            ▼
       ┌──────────────────────────────────────────────┐
       │              Dashboard (/dashboard/)         │
       └──────┬───────┬───────┬───────┬───────┬───────┘
              │       │       │       │       │
         ┌────▼┐ ┌────▼┐ ┌────▼┐ ┌────▼┐ ┌────▼┐ ┌────▼┐
         │Add  │ │Marks │ │Mark  │ │Student│ │QR   │ │QR   │
         │Marks│ │List  │ │Sheet │ │Analysis│ │Codes│ │Scan │
         └────┘ └────┘ └────┘ └──────┘ └────┘ └────┘
                     │                         │
                 ┌───▼───┐                 ┌───▼───┐
                 │Attendance               │Attendance│
                 │ List  │                 │ Report  │
                 └───────┘                 └─────────┘
```

## Tech Stack

- **Backend**: Django 5.x
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript
- **QR Codes**: qrcode library
- **Charts**: Chart.js

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start the development server:
```bash
python manage.py runserver
```

5. Access the application at `http://127.0.0.1:8000/`

## Project Structure

```
djangoacadstat/
├── academicsys/          # Main Django project
│   ├── settings.py       # Project settings
│   ├── urls.py           # URL routing
│   ├── views.py          # Main views
│   ├── templates/        # HTML templates
│   │   ├── dashboard/   # Dashboard pages
│   │   ├── registration/ # Login templates
│   │   └── admin/       # Admin templates
│   └── static/          # CSS, JS, images
├── core/                # Core app (models, views)
│   ├── models.py        # Database models
│   ├── views.py         # App views
│   ├── urls.py          # App URLs
│   └── migrations/      # Database migrations
└── manage.py            # Django management script
```

## Models

- **Student** - Stores student information with QR code
- **Subject** - Academic subjects
- **Result** - Student marks/grades
- **Attendance** - Attendance records
- **Teacher** - Teacher information

## URL Endpoints

| URL | Description |
|-----|-------------|
| `/` | Home page |
| `/login/` | User login |
| `/logout/` | User logout |
| `/dashboard/` | Main dashboard |
| `/add-marks/` | Add student marks |
| `/marks-list/` | View all marks |
| `/mark-sheet/` | Generate mark sheet |
| `/student-analysis/` | AI student analysis |
| `/qr-codes/` | Generate QR codes |
| `/qr-scanner/` | Scan QR codes |
| `/attendance/` | Attendance list |
| `/attendance-report/` | Attendance report |
| `/admin/` | Django admin |
