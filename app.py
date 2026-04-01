from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3
import re
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- إعدادات الموديل والقاعدة ---
model_path = 'medical_model.pkl'
DB_NAME = 'health_system_v2.db' # اسم جديد لتجنب تضارب البيانات القديمة

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
        # جدول المستخدمين مع الاسم الكامل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # جدول المواعيد الجديد
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                hospital TEXT NOT NULL,
                department TEXT NOT NULL,
                app_date TEXT NOT NULL,
                app_time TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

init_db()

# --- المسارات (Routes) ---

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', name=session.get('fullname'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fname = request.form.get('fullname', '').strip()
        user = request.form.get('username', '').strip()
        pwd = request.form.get('password', '').strip()
        
        # شروط الدكتور (8 خانات، رقم، رمز)
        if len(pwd) < 8 or not re.search(r"\d", pwd) or not re.search(r"[!@#$%^&*]", pwd):
            return "⚠️ خطأ: كلمة المرور يجب أن تكون 8 خانات وتحتوي على رقم ورمز خاص."
            
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cur = conn.cursor()
                cur.execute("INSERT OR REPLACE INTO users (fullname, username, password) VALUES (?, ?, ?)", (fname, user, pwd))
                conn.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return f"حدث خطأ: {e}"
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT fullname FROM users WHERE username = ? AND password = ?", (user, pwd))
            row = cur.fetchone()
            if row:
                session['username'] = user
                session['fullname'] = row[0]
                return redirect(url_for('home'))
    return render_template('login.html')

# --- حجز المواعيد ---
@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'username' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        hospital = request.form.get('hospital')
        dept = request.form.get('dept')
        date = request.form.get('date')
        time = request.form.get('time')
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username = ?", (session['username'],))
            u_id = cur.fetchone()[0]
            cur.execute("INSERT INTO appointments (user_id, hospital, department, app_date, app_time) VALUES (?, ?, ?, ?, ?)",
                        (u_id, hospital, dept, date, time))
            conn.commit()
        return "✅ تم حجز الموعد بنجاح! <a href='/'>العودة للرئيسية</a>"
    return render_template('book.html')

# --- باقي الصفحات ---
@app.route('/check')
def check(): return render_template('check.html')

@app.route('/bmi')
def bmi(): return render_template('bmi.html')

@app.route('/chronic')
def chronic(): return render_template('chronic.html')

@app.route('/meds')
def meds(): return render_template('meds.html')

@app.route('/skincare')
def skincare(): return render_template('skincare.html')

# --- التنبؤ بالذكاء الاصطناعي ---
@app.route('/predict', methods=['POST'])
def predict():
    try:
        age = float(request.form.get('age', 0))
        gl = float(request.form.get('glucose', 0))
        sys = float(request.form.get('systolic', 0))
        dia = float(request.form.get('diastolic', 0))
        if model:
            features = np.array([[age, gl, (sys+dia)/2]])
            pred = model.predict(features)
            res = "إيجابي" if pred[0] == 1 else "سلبي"
            st = "danger" if pred[0] == 1 else "success"
            tips = ["الالتزام بالدواء", "ممارسة الرياضة"] if pred[0] == 1 else ["حافظ على نشاطك", "أكثر من شرب الماء"]
            return render_template('result.html', result=res, tips=tips, status=st)
        return "الموديل غير جاهز."
    except Exception as e:
        return f"خطأ: {e}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
