from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
import csv
import random
from models import User
import logging
from sheets import get_google_sheets_data

app = Flask(__name__)
app.config.from_object('config.Config')

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    # Since we're using CSV for login, we need to manually load the user
    with open('usuarios.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row
        for row in reader:
            if row[0] == user_id:
                return User(username=row[0], password=row[1])
    return None

@app.route('/index')
@app.route('/')
def index():
    return redirect(url_for('login'))

def initialize_users():
    if not os.path.exists('usuarios.csv'):
        print("O arquivo usuarios.csv não foi encontrado.")
        return

    try:
        with open('usuarios.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row
            users = []
            for row in reader:
                if len(row) != 2:
                    print(f"Formato inválido na linha: {row}")
                    continue
                users.append(User(username=row[0], password=row[1]))
            return users
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")
        return []

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

        # Verifica o captcha
        if 'captcha_answer' not in session or int(captcha_response) != session['captcha_answer']:
            flash('Captcha inválido. Tente novamente.')
            return redirect(url_for('login'))

        users = initialize_users()
        user = next((u for u in users if u.username == username and u.password == password), None)

        if user:
            login_user(user)
            return redirect(url_for('dashboard_view'))
        else:
            flash('Esqueceu o login? ')

    # Gera uma nova conta para o captcha
    captcha_question, captcha_answer = generate_captcha()
    session['captcha_answer'] = captcha_answer

    return render_template('login.html', captcha_question=captcha_question)

@app.template_filter('currency_format')
def currency_format(value):
    if isinstance(value, str):
        try:
            value = float(value.replace('R$', '').replace(',', '').strip())
        except ValueError:
            return value  # In case the value is not a number, return it as is
    return f"R$ {value:,.2f}"

@app.route('/dashboard')
@login_required
def dashboard_view():
    email = current_user.username  # Assuming the username is the email
    logging.debug(f"Email do usuário logado: {email}")
    influenciador, data, total_a_receber, total_recebido, picture = get_google_sheets_data(email)
    logging.debug(f"Influenciador: {influenciador}, Data passed to template: {data}, Total a Receber: {total_a_receber}, Total Recebido: {total_recebido}, Picture: {picture}")
    
    # Prepare data for the chart
    dates = [row['data'] for row in data]
    values = [float(row['valor_influenciador'].replace('R$', '').replace(',', '').strip()) for row in data]
    
    return render_template('dashboard.html', user=current_user, influenciador=influenciador, data=data, total_a_receber=total_a_receber, total_recebido=total_recebido, picture=picture, dates=dates, values=values)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
