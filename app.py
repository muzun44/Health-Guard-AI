from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3

app = Flask(__name__)
app.secret_key = 'health_guard_secure_key'

# تحميل الموديل
try:
    model = pickle.load(open('medical_model.pkl', 'rb'))
except:
    model = None

# وظيفة للتعامل مع قاعدة البيانات
def get_db_connection():
    conn = sqlite3.connect('users_data.db')
    conn.row_factory = sqlite3.Row
    return conn

# إنشاء جدول المستخدمين إذا لم يكن موجوداً
def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
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
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            return "اسم المستخدم موجود مسبقاً، اختر اسماً آخر."
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            error = 'بيانات الدخول خاطئة'
    return render_template('login.html', error=error)

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session: return redirect(url_for('login'))
    try:
        age = float(request.form.get('age'))
        glucose = float(request.form.get('glucose'))
        systolic = float(request.form.get('systolic'))
        diastolic = float(request.form.get('diastolic'))
        bp_avg = (systolic + diastolic) / 2
        
        features = np.array([[age, glucose, bp_avg]])
        prediction = model.predict(features)
        
        res = "إيجابي" if prediction[0] == 1 else "سلبي"
        adv = "نصيحة: قلل السكريات وراجع الطبيب." if prediction[0] == 1 else "نصيحة: حالتك ممتازة، استمر."
        st = "danger" if prediction[0] == 1 else "success"
        
        return render_template('result.html', result=res, advice=adv, status=st)
    except:
        return "خطأ في البيانات"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
