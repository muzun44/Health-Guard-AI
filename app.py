from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3
import re
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) # مفتاح أمان متغير

# تحميل الموديل بذكاء لتجنب الانهيار
model = None
if os.path.exists('medical_model.pkl'):
    try:
        with open('medical_model.pkl', 'rb') as f:
            model = pickle.load(f)
    except Exception as e:
        print(f"Error loading model: {e}")

DB_NAME = 'health_database_v4.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', user=session['username'])
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pwd = request.form.get('password', '').strip()
        
        # شروط الدكتور
        if len(pwd) < 8:
            return "خطأ: كلمة المرور قصيرة جداً (أقل من 8)."
        if not re.search(r"\d", pwd):
            return "خطأ: يجب وجود رقم واحد على الأقل."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>+-]", pwd):
            return "خطأ: يجب وجود رمز خاص واحد على الأقل."
            
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
                conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "هذا الاسم موجود، اختر اسماً آخر."
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pwd = request.form.get('password', '').strip()
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (user, pwd))
            if cur.fetchone():
                session['username'] = user
                return redirect(url_for('home'))
            else:
                error = 'بيانات الدخول خاطئة.'
    return render_template('login.html', error=error)

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session: return redirect(url_for('login'))
    try:
        age = float(request.form.get('age', 0))
        glucose = float(request.form.get('glucose', 0))
        systolic = float(request.form.get('systolic', 0))
        diastolic = float(request.form.get('diastolic', 0))
        bp_avg = (systolic + diastolic) / 2
        
        if model:
            pred = model.predict(np.array([[age, glucose, bp_avg]]))[0]
            if pred == 1:
                res, st = "إيجابي (احتمال إصابة)", "danger"
                tips = ["قلل السكريات", "راقب الضغط", "مارس الرياضة", "استشر طبيباً"]
            else:
                res, st = "سلبي (الحالة مستقرة)", "success"
                tips = ["غذاء غني بالألياف", "شرب الماء", "نشاط بدني", "فحص دوري"]
            return render_template('result.html', result=res, tips=tips, status=st)
        return "الموديل غير متاح."
    except Exception as e:
        return f"خطأ في البيانات: {e}"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
