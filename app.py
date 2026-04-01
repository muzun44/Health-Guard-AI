  from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3
import re
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- إعدادات القاعدة والموديل ---
DB_NAME = 'health_system_final.db'
model_path = 'medical_model.pkl'

model = None
if os.path.exists(model_path):
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
    except:
        pass

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, fullname TEXT, username TEXT UNIQUE, password TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS appointments 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, hospital TEXT, 
            department TEXT, app_date TEXT, app_time TEXT, FOREIGN KEY(user_id) REFERENCES users(id))''')
        conn.commit()

init_db()

@app.route('/')
def home():
    if 'username' in session:
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username = ?", (session['username'],))
            u_id = cur.fetchone()[0]
            cur.execute("SELECT hospital, department, app_date, app_time FROM appointments WHERE user_id = ?", (u_id,))
            apps = cur.fetchall()
        return render_template('index.html', name=session.get('fullname'), appointments=apps)
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fn = request.form.get('fullname')
        un = request.form.get('username')
        pw = request.form.get('password')
        if len(pw) < 8 or not re.search(r"\d", pw) or not re.search(r"[!@#$%^&*]", pw):
            return "خطأ: كلمة المرور ضعيفة (8 خانات، رقم، رمز)."
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cur = conn.cursor()
                cur.execute("INSERT OR REPLACE INTO users (fullname, username, password) VALUES (?, ?, ?)", (fn, un, pw))
                conn.commit()
            return redirect(url_for('login'))
        except: return "اليوزر موجود مسبقاً."
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        un = request.form.get('username')
        pw = request.form.get('password')
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT fullname FROM users WHERE username=? AND password=?", (un, pw))
            row = cur.fetchone()
            if row:
                session['username'], session['fullname'] = un, row[0]
                return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'username' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        h, d, dt, tm = request.form.get('hospital'), request.form.get('dept'), request.form.get('date'), request.form.get('time')
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username=?", (session['username'],))
            u_id = cur.fetchone()[0]
            cur.execute("INSERT INTO appointments (user_id, hospital, department, app_date, app_time) VALUES (?, ?, ?, ?, ?)", (u_id, h, d, dt, tm))
            conn.commit()
        return redirect(url_for('home'))
    return render_template('book.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        age, gl = float(request.form.get('age')), float(request.form.get('glucose'))
        sys, dia = float(request.form.get('systolic')), float(request.form.get('diastolic'))
        if model:
            res = model.predict(np.array([[age, gl, (sys+dia)/2]]))[0]
            st = "danger" if res == 1 else "success"
            msg = "إيجابي" if res == 1 else "سلبي"
            tips = ["حمية غذائية", "رياضة"] if res == 1 else ["استمر بنشاطك"]
            return render_template('result.html', result=msg, status=st, tips=tips)
    except: return "خطأ في البيانات."

@app.route('/check')
def check(): return render_template('check.html')

@app.route('/bmi')
def bmi(): return render_template('bmi.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
