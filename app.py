from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'health_guard_final_key_2026'

# 1. تحميل موديل الذكاء الاصطناعي
try:
    model = pickle.load(open('medical_model.pkl', 'rb'))
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# 2. وظائف قاعدة البيانات (تم تغيير الاسم لضمان التصفير)
DB_NAME = 'final_medical_system.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# تشغيل إنشاء قاعدة البيانات فوراً
init_db()

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', user=session['username'])
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = request.form.get('username').strip()
        pwd = request.form.get('password').strip()
        
        if not user or not pwd:
            return "الرجاء إدخال اسم مستخدم وكلمة مرور"
            
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "هذا الاسم مسجل مسبقاً، جرب اسماً آخر (مثل إضافة رقم لاسمك)."
        except Exception as e:
            return f"حدث خطأ غير متوقع: {e}"
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form.get('username').strip()
        pwd = request.form.get('password').strip()
        
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (user, pwd))
        found_user = cur.fetchone()
        conn.close()
        
        if found_user:
            session['username'] = user
            return redirect(url_for('home'))
        else:
            error = 'بيانات الدخول غير صحيحة، تأكد من الاسم وكلمة المرور.'
    return render_template('login.html', error=error)

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        # التأكد من وصول البيانات من الفورم
        age = float(request.form.get('age', 0))
        glucose = float(request.form.get('glucose', 0))
        systolic = float(request.form.get('systolic', 0))
        diastolic = float(request.form.get('diastolic', 0))
        
        # حساب متوسط الضغط كما يتوقع الموديل
        bp_avg = (systolic + diastolic) / 2
        
        if model:
            features = np.array([[age, glucose, bp_avg]])
            prediction = model.predict(features)
            
            if prediction[0] == 1:
                res, adv, st = "إيجابي (احتمال إصابة)", "نصيحة: قلل السكريات والملح وراجع الطبيب للطمأنينة.", "danger"
            else:
                res, adv, st = "سلبي (الحالة مستقرة)", "نصيحة: استمر في ممارسة الرياضة ونظامك الغذائي الصحي.", "success"
        else:
            res, adv, st = "خطأ", "ملف الموديل مفقود، تأكد من رفعه على GitHub.", "warning"
            
        return render_template('result.html', result=res, advice=adv, status=st)
    except Exception as e:
        return f"خطأ في معالجة البيانات: {e}"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
