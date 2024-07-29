import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

def get_google_sheets_data(email):
    try:
        # Define the scope
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # Add credentials to the account
        creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret_25408069079-1950nq3ke61reuafoqauccdr5lk1eeem.apps.googleusercontent.com.json", scope)

        # Authorize the clientsheet 
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
