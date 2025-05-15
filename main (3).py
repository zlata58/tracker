from flask import Flask, render_template, redirect, url_for, request, flash
from forms.registerform import RegisterForm
from forms.loginform import LoginForm
from data import db_session
from data.users import User
from flask_login import LoginManager, login_user, logout_user, login_required
import sqlite3
from pathlib import Path

app = Flask(__name__)

app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db_session.global_init("db/blogs.db")

db_path = Path('instance') / 'habits.db'
db_path.parent.mkdir(exist_ok=True)  # Создаем папку instance если её нет
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password2.data:
            return render_template('register.html', title='Register',
                                   form=form,
                                   message="Пароли не совпадают")
        if len(form.password.data) < 6 and len(form.password2.data) < 6:
            return render_template('register.html', title='Register',
                                   form=form,
                                   message="Пароль должен быть минимум из 6 символов!")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Register',
                                   form=form, message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect(url_for('homepage'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Данные некорректны",
                               form=form)
    return render_template('login.html', title='Login', form=form)
    if form.validate_on_submit_reg():
        return render_template('register.html', title='Register', form=form)
    return redirect(url_for('homepage'))

@app.route("/habittracker")
@app.route("/", methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        new_habit = request.form.get('habit').strip()
        if new_habit:
            try:
                conn = sqlite3.connect('instance/habits.db')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO habits (name) VALUES (?)', (new_habit,))
                conn.commit()
                flash('Привычка успешно добавлена!', 'success')
            except Exception as e:
                flash(f'Ошибка: {str(e)}', 'danger')
            return redirect(url_for('homepage'))

    # Получаем все привычки для отображения
    habits = []
    try:
        conn = sqlite3.connect('instance/habits.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM habits ORDER BY created_at DESC')
        habits = [row[0] for row in cursor.fetchall()]
    except:
        habits = []
    return render_template("homepage.html", habits=habits)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
    app.run(port=8000, host='127.0.0.1')