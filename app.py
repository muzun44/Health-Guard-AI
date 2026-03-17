import re # سنحتاج هذه المكتبة للتحقق من الرموز

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = request.form.get('username').strip()
        pwd = request.form.get('password').strip()
        
        # شروط الدكتور:
        # 1. طول الكلمة لا يقل عن 8
        # 2. تحتوي على رقم واحد على الأقل
        # 3. تحتوي على رمز خاص واحد على الأقل
        if len(pwd) < 8:
            return "خطأ: كلمة المرور يجب أن تكون 8 خانات على الأقل."
        if not re.search(r"\d", pwd):
            return "خطأ: كلمة المرور يجب أن تحتوي على رقم واحد على الأقل."
        if not re.search(r"[ !@#$%^&*(),.?\":{}|<>+-]", pwd):
            return "خطأ: كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل (مثل @، #، $)."
            
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "هذا الاسم مسجل مسبقاً."
    return render_template('signup.html')
