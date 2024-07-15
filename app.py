from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
import csv
import random
import requests
from models import db, User
import config
import mysql.connector
import logging

app = Flask(__name__)
app.config.from_object(config.Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/index')
@app.route('/')
def index():
    return redirect(url_for('login'))

def reset_database():
    db.drop_all()
    db.create_all()

def initialize_users():
    if not os.path.exists('usuarios.csv'):
        print("O arquivo usuarios.csv não foi encontrado.")
        return

    try:
        with open('usuarios.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row
            for row in reader:
                if len(row) != 2:
                    print(f"Formato inválido na linha: {row}")
                    continue
                username, password = row
                if not User.query.filter_by(username=username).first():
                    new_user = User(username=username, password=password)
                    db.session.add(new_user)
            db.session.commit()
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")

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

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard_view'))
        else:
            flash('Esqueceu o login? ')

    # Gera uma nova conta para o captcha
    captcha_question, captcha_answer = generate_captcha()
    session['captcha_answer'] = captcha_answer

    return render_template('login.html', captcha_question=captcha_question)

def get_faturamento_publicidade(email):
    try:
        connection = mysql.connector.connect(
            host="database-1.cedwytewklqg.us-east-1.rds.amazonaws.com",
            user="admin",
            password="Curta123",
            database="curta_analytics"
        )
        cursor = connection.cursor()
        query = """
        SELECT
            reports.influenciador,
            reports.data,
            reports.marca,
            reports.campanha,
            reports.valor_influenciador,
            reports.status_pgt_,
            pic.picture
        FROM
            curta_analytics.reports_influ_beta2 AS reports
        LEFT JOIN
            curta_analytics.influenciadores_mkdigital_2024 AS pic
        ON
            reports.influenciador = pic.name
        WHERE
            reports.e_mail_influ = %s
        LIMIT 100;
        """
        cursor.execute(query, (email,))
        results = cursor.fetchall()
        logging.debug(f"Number of records fetched: {len(results)}")
        logging.debug(f"Data retrieved: {results}")
        cursor.close()
        connection.close()

        if results:
            influenciador = results[0][0]
            picture = results[0][6]
            data = [row[1:6] for row in results]
            
            total_a_receber = 0
            total_recebido = 0
            
            for row in results:
                valor = row[4].replace('R$', '').replace(',', '').strip()
                valor_float = float(valor) if valor else 0.0
                
                if row[5] == "Aguardando":
                    total_a_receber += valor_float
                elif row[5] == "OK":
                    total_recebido += valor_float

            return influenciador, data, total_a_receber, total_recebido, picture
        else:
            return None, [], 0, 0, None

    except mysql.connector.Error as err:
        logging.error(f"Error: {err}")
        return None, [], 0, 0, None

@app.route('/dashboard')
@login_required
def dashboard_view():
    email = current_user.username  # Assuming the username is the email
    logging.debug(f"Email do usuário logado: {email}")
    influenciador, data, total_a_receber, total_recebido, picture = get_faturamento_publicidade(email)
    logging.debug(f"Influenciador: {influenciador}, Data passed to template: {data}, Total a Receber: {total_a_receber}, Total Recebido: {total_recebido}, Picture: {picture}")

    # Power BI embed URL
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
    logging.basicConfig(level=logging.DEBUG)
    with app.app_context():
        reset_database()
        initialize_users()
    app.run(debug=True)
