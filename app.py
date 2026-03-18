from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3
import re
import os

app = Flask(__name__)
app.secret_key = 'health_guard_mega_system_2026'

# --- إعدادات الموديل والقاعدة ---
model = None
if os.path.exists('medical_model.pkl'):
    try:
        with open('medical_model.pkl', 'rb') as f:
            model = pickle.load(f)
    except: model = None

DB_NAME = 'full_health_system.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
init_db()

# --- المسارات الأساسية (التسجيل والدخول) ---
@app.route('/')
def home():
    if 'username' in session: return render_template('index.html', user=session['username'])
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user, pwd = request.form.get('username', '').strip(), request.form.get('password', '').strip()
        # شروط الدكتور (8 خانات، رقم، رمز)
        if len(pwd) < 8 or not re.search(r"\d", pwd) or not re.search(r"[!@#$%^&*]", pwd):
            return "خطأ: تأكد من شروط كلمة المرور (8 خانات، رقم، رمز خاص)."
        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
            return redirect(url_for('login'))
        except: return "الاسم موجود مسبقاً."
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user, pwd = request.form.get('username', '').strip(), request.form.get('password', '').strip()
        with sqlite3.connect(DB_NAME) as conn:
            if conn.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd)).fetchone():
                session['username'] = user
                return redirect(url_for('home'))
        return "بيانات خاطئة."
    return render_template('login.html')

# --- المسارات الجديدة (الأقسام التي طلبتِها) ---

@app.route('/check') # صفحة فحص السكر والضغط بالذكاء الاصطناعي
def check():
    return render_template('check.html')

@app.route('/chronic') # قسم الأمراض المزمنة
def chronic():
    return render_template('chronic.html')

@app.route('/bmi') # قسم الوزن والكتلة
def bmi():
    return render_template('bmi.html')

@app.route('/meds') # قسم الصيدلية والأدوية
def meds():
    return render_template('meds.html')

@app.route('/skincare') # قسم البشرة
def skincare():
    return render_template('skincare.html')

# --- منطق التنبؤ بالذكاء الاصطناعي ---
@app.route('/predict', methods=['POST'])
def predict():
    try:
        age = float(request.form.get('age', 0))
        glucose = float(request.form.get('glucose', 0))
        systolic = float(request.form.get('systolic', 0))
        diastolic = float(request.form.get('diastolic', 0))
        bp_avg = (systolic + diastolic) / 2
        if model:
            pred = model.predict(np.array([[age, glucose, bp_avg]]))[0]
            res, st = ("إيجابي", "danger") if pred == 1 else ("سلبي", "success")
            tips = ["نصيحة 1", "نصيحة 2"] # يمكن تخصيصها لاحقاً
            return render_template('result.html', result=res, tips=tips, status=st)
        return "الموديل غير متاح."
    except: return "خطأ في البيانات."

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
