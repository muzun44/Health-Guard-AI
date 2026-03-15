from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np

app = Flask(__name__)
app.secret_key = 'health_guard_secret'

model = pickle.load(open('medical_model.pkl', 'rb'))

@app.route('/')
def home():
    if 'logged_in' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '12345':
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = 'بيانات الدخول غير صحيحة'
    return render_template('login.html', error=error)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # قراءة البيانات والتأكد من تحويلها لأرقام
        age = float(request.form.get('age', 0))
        glucose = float(request.form.get('glucose', 0))
        systolic = float(request.form.get('systolic', 0))
        diastolic = float(request.form.get('diastolic', 0))
        
        # حساب متوسط الضغط
        bp_average = (systolic + diastolic) / 2
        
        features = np.array([[age, glucose, bp_average]])
        prediction = model.predict(features)
        
        if prediction[0] == 1:
            result_text = "إيجابي (احتمال وجود إصابة)"
            advice = "نصيحة: قلل السكريات وراجع الطبيب."
            status = "danger"
        else:
            result_text = "سلبي (الحالة مستقرة)"
            advice = "نصيحة: استمر في نمط حياتك الصحي."
            status = "success"
            
        return render_template('result.html', result=result_text, advice=advice, status=status)
    except Exception as e:
        return f"حدث خطأ في البيانات: {e}"

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if name == '__main__':
    app.run(debug=True)
