from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import os
import csv
import random
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.config.from_object('config.Config')

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define a User class to work with Flask-Login
class User(UserMixin):
    def __init__(self, username, password):
        self.id = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    users = initialize_users()
    for user in users:
        if user.id == user_id:
            return user
    return None

def initialize_users():
    users = []
    if not os.path.exists('usuarios.csv'):
        print("O arquivo usuarios.csv não foi encontrado.")
        return users

    try:
        with open('usuarios.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row
            for row in reader:
                if len(row) != 2:
                    print(f"Formato inválido na linha: {row}")
                    continue
                users.append(User(username=row[0], password=row[1]))
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")
    return users

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
        user = next((u for u in users if u.id == username and u.password == password), None)

        if user:
            login_user(user)
            return redirect(url_for('dashboard_view'))
        else:
            flash('Credenciais inválidas. Tente novamente.')

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

def get_google_sheets_data(email):
    try:
        # Define the scope
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # Add credentials to the account
        creds = ServiceAccountCredentials.from_json_keyfile_name("relatoriosTeste.json", scope)

        # Authorize the client
        client = gspread.authorize(creds)

        # Get the Base3 sheet
        sheet = client.open("relatorios teste").worksheet("Base3")

        # Get all the records of the data
        records = sheet.get_all_records()

        # Filter data by email
        data = [record for record in records if record['e_mail_influ'] == email]

        if data:
            influenciador = data[0]['influenciador']
            picture = data[0]['picture']
            total_a_receber = sum(float(record['valor_influenciador'].replace('R$', '').replace(',', '').strip()) for record in data if record['status_pgt_'] == "Aguardando")
            total_recebido = sum(float(record['valor_influenciador'].replace('R$', '').replace(',', '').strip()) for record in data if record['status_pgt_'] == "OK")

            return influenciador, data, total_a_receber, total_recebido, picture
        else:
            return None, [], 0.0, 0.0, None

    except Exception as e:
        logging.error(f"Error: {e}")
        return None, [], 0.0, 0.0, None

@app.route('/dashboard')
@login_required
def dashboard_view():
    email = current_user.id  # Assuming the username is the email
    logging.debug(f"Email do usuário logado: {email}")
    
    influenciador, data, total_a_receber, total_recebido, picture = get_google_sheets_data(email)
    logging.debug(f"Influenciador: {influenciador}, Data passed to template: {data}, Total a Receber: {total_a_receber}, Total Recebido: {total_recebido}, Picture: {picture}")
    
    if not data:
        logging.debug("No data available to display on the dashboard.")
    
    # Prepare data for the chart
    dates = [row.get('data') for row in data]
    values = [safe_convert(row.get('valor_influenciador', '0')) for row in data]

    return render_template('dashboard.html', user=current_user, influenciador=influenciador, data=data, total_a_receber=total_a_receber, total_recebido=total_recebido, picture=picture, dates=dates, values=values)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
