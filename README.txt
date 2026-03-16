
Academic Analytics System
Tech Stack:
HTML, CSS, Bootstrap
Django Auth
Django ORM
Python Logic
Chart.js
PostgreSQL

Run Instructions:

1. Install dependencies
pip install django psycopg2

2. Create PostgreSQL database
CREATE DATABASE academics_db;

3. Run migrations
python manage.py makemigrations
python manage.py migrate

4. Create admin user
python manage.py createsuperuser

5. Run server
python manage.py runserver

6. Open browser
http://127.0.0.1:8000
