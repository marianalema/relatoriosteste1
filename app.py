from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
import csv
import random
import logging

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('login'))

def generate_captcha():
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    question = f"{num1} + {num2} = ?"
    answer = num1 + num2
    return question, answer

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        captcha_response = request.form.get('captcha')

        if 'captcha_answer' not in session or int(captcha_response) != session['captcha_answer']:
            flash('Invalid captcha. Please try again.')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard_view'))
        else:
            flash('Incorrect login details.')

    captcha_question, captcha_answer = generate_captcha()
    session['captcha_answer'] = captcha_answer

    return render_template('login.html', captcha_question=captcha_question)

@app.route('/dashboard')
@login_required
def dashboard_view():
    email = current_user.username
    # Assuming get_faturamento_publicidade is implemented elsewhere in your code
    influenciador, data, total_a_receber, total_recebido, picture = get_faturamento_publicidade(email)

    power_bi_embed_url = "https://app.powerbi.com/reportEmbed?reportId=3b05e3a8-e10b-4f63-8328-1241ef31e17e&autoAuth=true&ctid=3efff910-7dd6-45b1-ab3c-6f7351e8346a"

    return render_template('dashboard.html',
                           user=current_user,
                           influenciador=influenciador,
                           data=data,
                           total_a_receber=total_a_receber,
                           total_recebido=total_recebido,
                           picture=picture,
                           power_bi_embed_url=power_bi_embed_url)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
