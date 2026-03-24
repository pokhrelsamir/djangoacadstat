
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


===============================================
STUDENT LOGIN SETUP
===============================================

To allow students to login and view their own dashboard, you need to create 
Django user accounts for them. Here are the commands:

1. CREATE A SINGLE STUDENT USER:
   python manage.py create_student_user <student_id> <password>
   
   Example:
   python manage.py create_student_user 1 mypassword123

2. CREATE USERS FOR ALL STUDENTS:
   python manage.py create_all_student_users --password student123
   
   Options:
   --password: Set the password for all accounts (default: student123)
   --prefix: Add a prefix to usernames (e.g., --prefix "stu_" makes "stu_ram")

3. HOW IT WORKS:
   - The student's name becomes their username
   - When they login, they are redirected to their personal dashboard
   - They can see their own QR code, marks, attendance, and performance charts
   - They CANNOT access admin features like Add Marks, QR Scanner, etc.

4. LOGIN URL:
   http://127.0.0.1:8000/login/


===============================================
MARK SHEET GENERATION
===============================================

1. Go to Dashboard > View Mark Sheet
2. Select a student
3. Select the terminal (1st, 2nd, 3rd, or Final)
4. Click "Generate Mark Sheet"
5. The mark sheet shows:
   - Student information
   - Marks with Pass (P) for ≥40% and Fail (F) for <40%
   - Total marks calculated from all subjects
   - Overall percentage and pass/fail status


===============================================
ADDING TERMINAL MARKS
===============================================

When adding marks, select the terminal (1st, 2nd, 3rd, or Final) from the 
visual selector. Each terminal exam is tracked separately.


===============================================
FEATURES
===============================================

✓ Student Management (Admin)
✓ Subject Management (Admin)
✓ Marks Entry with Terminal Selection
✓ Mark Sheet Generation with Pass/Fail Grades
✓ QR Code Attendance System
✓ Student Dashboard with Charts
✓ Performance Analytics by Terminal
✓ Theme Toggle (Light/Dark)
✓ OCR-Ready Mark Sheet Format
