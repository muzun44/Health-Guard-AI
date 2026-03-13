from flask import Flask, render_template, request
import pickle

app = Flask(__name__)

# تحميل الموديل - تأكدي أن الملف بنفس الاسم في مجلد المشروع
model = pickle.load(open('medical_model.pkl', 'rb'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        age = float(request.form['age'])
        glucose = float(request.form['glucose'])
        bp = float(request.form['blood_pressure'])
        
        prediction = model.predict([[age, glucose, bp]])
        result_text = "High Risk" if prediction[0] == 1 else "Low Risk"
        
        return render_template('result.html', result=result_text)
    except:
        return "Error in data entry. Please try again."

if __name__ == "__main__":
    app.run(debug=True)