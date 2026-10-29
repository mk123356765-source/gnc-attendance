import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

try:
    import qrcode
except ImportError:
    qrcode = None

app = Flask(__name__)
app.secret_key = "gov_national_college_key_2026"

# --- SQLITE DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    # Create Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            roll_no TEXT PRIMARY KEY,
            name TEXT,
            cnic TEXT UNIQUE,
            dept TEXT
        )
    ''')
    # Create Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            date TEXT,
            FOREIGN KEY(roll_no) REFERENCES students(roll_no)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB on start
init_db()

# SECURITY CREDENTIALS
REG_USER = "admin"
REG_PASS = "gnc123"
PRINCIPAL_USER = "principal"
PRINCIPAL_PASS = "gnc@principal2026"

daily_credentials = {
    "username": "gnc_today",
    "password": "change_me_daily"
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')
        
        if user == REG_USER and password == REG_PASS:
            name = request.form.get('name')
            roll_no = request.form.get('roll_no').strip()
            cnic = request.form.get('cnic').strip()
            dept = request.form.get('dept')
            
            # --- DATABASE DUPLICATE VALIDATION ---
            conn = sqlite3.connect('college.db')
            cursor = conn.cursor()
            
            # Check Roll Number
            cursor.execute('SELECT * FROM students WHERE roll_no = ?', (roll_no,))
            if cursor.fetchone():
                flash("Error: This Roll Number is already registered!")
                conn.close()
                return render_template('register.html')
                
            # Check CNIC
            cursor.execute('SELECT * FROM students WHERE cnic = ?', (cnic,))
            if cursor.fetchone():
                flash("Error: This CNIC / B-Form Number is already registered!")
                conn.close()
                return render_template('register.html')
            
            # Insert new student if unique
            cursor.execute('INSERT INTO students (roll_no, name, cnic, dept) VALUES (?, ?, ?, ?)', (roll_no, name, cnic, dept))
            conn.commit()
            conn.close()
            
            # Generate QR Code
            if not os.path.exists('static/qrcodes'):
                os.makedirs('static/qrcodes')
                
            qr_path = f"static/qrcodes/{roll_no}.png"
            if qrcode:
                qr_img = qrcode.make(roll_no)
                qr_img.save(qr_path)
            
            return render_template('card.html', name=name, roll_no=roll_no, cnic=cnic, dept=dept, qr_path=qr_path)
        else:
            flash("Invalid Registration System Access Credentials!")
            
    return render_template('register.html')

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if request.method == 'POST':
        u_name = request.form.get('daily_user')
        u_pass = request.form.get('daily_pass')
        roll_no = request.form.get('roll_no').strip()
        
        if u_name == daily_credentials['username'] and u_pass == daily_credentials['password']:
            conn = sqlite3.connect('college.db')
            cursor = conn.cursor()
            
            # Check if student exists
            cursor.execute('SELECT name FROM students WHERE roll_no = ?', (roll_no,))
            student = cursor.fetchone()
            
            if student:
                from datetime import datetime
                today_date = datetime.now().strftime('%Y-%m-%d')
                
                # Check if already marked today
                cursor.execute('SELECT * FROM attendance WHERE roll_no = ? AND date = ?', (roll_no, today_date))
                if cursor.fetchone():
                    conn.close()
                    return render_template('attendance_status.html', success=False, msg="Attendance already marked for today!")
                
                # Mark present
                cursor.execute('INSERT INTO attendance (roll_no, date) VALUES (?, ?)', (roll_no, today_date))
                conn.commit()
                conn.close()
                return render_template('attendance_status.html', success=True, msg=f"Attendance Marked Successfully for {student[0]} (Roll: {roll_no})!")
            else:
                conn.close()
                return render_template('attendance_status.html', success=False, msg="Roll Number not found! Please register first.")
        else:
            return render_template('attendance_status.html', success=False, msg="Access Denied: Invalid Daily Campus Credentials.")
            
    return render_template('attendance.html')

@app.route('/principal-panel', methods=['GET', 'POST'])
def principal_panel():
    if request.method == 'POST':
        p_user = request.form.get('principal_user')
        p_pass = request.form.get('principal_pass')
        
        if p_user == PRINCIPAL_USER and p_pass == PRINCIPAL_PASS:
            daily_credentials['username'] = request.form.get('new_user')
            daily_credentials['password'] = request.form.get('new_pass')
            flash("Daily campus credentials updated successfully!")
        else:
            flash("Access Denied: Invalid Principal Credentials.")
            
    return render_template('principal.html', current_user=daily_credentials['username'], current_pass=daily_credentials['password'])

@app.route('/teacher-panel')
def teacher_panel():
    return render_template('teacher.html', current_user=daily_credentials['username'], current_pass=daily_credentials['password'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
