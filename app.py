from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3
import re # لمكتبة التحقق من شروط كلمة المرور

app = Flask(__name__)
app.secret_key = 'health_guard_pro_key_2026'

# تحميل الموديل
try:
    model = pickle.load(open('medical_model.pkl', 'rb'))
except:
    model = None

DB_NAME = 'health_system_v3.db'

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
        
        # تطبيق شروط الدكتور (Security Validation)
        if len(pwd) < 8:
            return "خطأ: كلمة المرور يجب أن تكون 8 خانات على الأقل."
        if not re.search(r"\d", pwd):
            return "خطأ: يجب أن تحتوي كلمة المرور على رقم واحد على الأقل."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>+-]", pwd):
            return "خطأ: يجب أن تحتوي كلمة المرور على رمز خاص واحد على الأقل (@#$)."
            
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "هذا الاسم مسجل مسبقاً، حاول باسم آخر."
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
            error = 'بيانات الدخول غير صحيحة.'
    return render_template('login.html', error=error)

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        age = float(request.form.get('age', 0))
        glucose = float(request.form.get('glucose', 0))
        systolic = float(request.form.get('systolic', 0))
        diastolic = float(request.form.get('diastolic', 0))
        bp_avg = (systolic + diastolic) / 2
        
        if model:
            features = np.array([[age, glucose, bp_avg]])
            prediction = model.predict(features)
            
            if prediction[0] == 1:
                res = "إيجابي (احتمال إصابة)"
                # نظام النصائح الذكي للحالات الإيجابية
                tips = [
                    "تقليل استهلاك السكريات والنشويات فوراً.",
                    "مراقبة ضغط الدم بشكل يومي وتسجيل القراءات.",
                    "المشي لمدة 30 دقيقة يساعد في تحسين النتائج.",
                    "يُرجى استشارة طبيب مختص للقيام بفحوصات أدق."
                ]
                st = "danger"
            else:
                res = "سلبي (الحالة مستقرة)"
                # نظام النصائح الوقائي
                tips = [
                    "حافظ على نظام غذائي غني بالألياف والخضروات.",
                    "شرب الماء بكميات كافية (8 أكواب يومياً).",
                    "الاستمرار في النشاط البدني لتعزيز المناعة.",
                    "الفحص الدوري كل 6 أشهر إجراء وقائي ممتاز."
                ]
                st = "success"
        else:
            return "الموديل غير متاح حالياً."
            
        return render_template('result.html', result=res, tips=tips, status=st)
    except Exception as e:
        return f"خطأ في البيانات: {e}"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
