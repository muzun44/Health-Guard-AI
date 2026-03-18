from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3
import re
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) # مفتاح أمان لضمان عمل الجلسات (Sessions)

# --- تحميل موديل الذكاء الاصطناعي ---
model = None
model_path = 'medical_model.pkl'
if os.path.exists(model_path):
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
    except Exception as e:
        print(f"خطأ في تحميل الموديل: {e}")

# --- إعداد قاعدة بيانات المستخدمين ---
DB_NAME = 'health_guard_system.db'

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

# --- المسارات الأساسية (الرئيسية والدخول) ---

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
        
        # شروط الدكتور للأمان (8 خانات، رقم، رمز خاص)
        if len(pwd) < 8:
            return "خطأ: كلمة المرور يجب أن تكون 8 خانات على الأقل."
        if not re.search(r"\d", pwd):
            return "خطأ: يجب أن تحتوي كلمة المرور على رقم واحد على الأقل."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>+-]", pwd):
            return "خطأ: يجب أن تحتوي كلمة المرور على رمز خاص واحد على الأقل."
            
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
                conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "اسم المستخدم مسجل مسبقاً، جرب اسماً آخر."
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
                error = 'بيانات الدخول غير صحيحة.'
    return render_template('login.html', error=error)

# --- مسارات الأقسام الجديدة ---

@app.route('/check')
def check():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template('check.html')

@app.route('/bmi')
def bmi():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template('bmi.html')

@app.route('/chronic')
def chronic():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template('chronic.html')

@app.route('/meds')
def meds():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template('meds.html')

@app.route('/skincare')
def skincare():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template('skincare.html')

# --- منطق فحص الذكاء الاصطناعي (AI Prediction) ---

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session: return redirect(url_for('login'))
    try:
        age = float(request.form.get('age', 0))
        glucose = float(request.form.get('glucose', 0))
        systolic = float(request.form.get('systolic', 0))
        diastolic = float(request.form.get('diastolic', 0))
        
        # حساب متوسط الضغط
        bp_avg = (systolic + diastolic) / 2
        
        if model:
            # تحويل البيانات لتنسيق المصفوفة لـ Numpy
            features = np.array([[age, glucose, bp_avg]])
            prediction = model.predict(features)
            
            if prediction[0] == 1:
                res, st = "إيجابي (احتمال إصابة)", "danger"
                tips = ["تقليل السكريات والنشويات", "مراقبة الضغط يومياً", "ممارسة المشي بانتظام", "استشارة طبيب مختص"]
            else:
                res, st = "سلبي (الحالة مستقرة)", "success"
                tips = ["غذاء غني بالألياف", "شرب الماء بكثرة", "النشاط البدني المستمر", "الفحص الدوري الوقائي"]
            
            return render_template('result.html', result=res, tips=tips, status=st)
        else:
            return "خطأ: الموديل الذكي غير جاهز حالياً."
    except Exception as e:
        return f"خطأ في معالجة البيانات: {str(e)}"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
