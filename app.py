 from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3

app = Flask(__name__)
app.secret_key = 'health_guard_ultra_secret'

# تحميل الموديل
try:
    model = pickle.load(open('medical_model.pkl', 'rb'))
except:
    model = None

# إنشاء قاعدة البيانات تلقائياً
def init_db():
    conn = sqlite3.connect('users.db')
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
        user = request.form['username']
        pwd = request.form['password']
        try:
            conn = sqlite3.connect('users.db')
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            return "اسم المستخدم موجود مسبقاً، حاول باسم آخر."
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (user, pwd))
        found_user = cur.fetchone()
        conn.close()
        if found_user:
            session['username'] = user
            return redirect(url_for('home'))
        else:
            error = 'بيانات الدخول غير صحيحة'
    return render_template('login.html', error=error)

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        age = float(request.form.get('age'))
        glucose = float(request.form.get('glucose'))
        systolic = float(request.form.get('systolic'))
        diastolic = float(request.form.get('diastolic'))
        bp_avg = (systolic + diastolic) / 2
        features = np.array([[age, glucose, bp_avg]])
        prediction = model.predict(features)
        
        if prediction[0] == 1:
            res, adv, st = "إيجابي", "نصيحة: قلل السكريات وراجع الطبيب.", "danger"
        else:
            res, adv, st = "سلبي", "نصيحة: حالتك ممتازة، استمر في نمط حياتك الصحي.", "success"
            
        return render_template('result.html', result=res, advice=adv, status=st)
    except:
        return "خطأ في إدخال البيانات"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if name == '__main__':
    app.run(debug=True)
