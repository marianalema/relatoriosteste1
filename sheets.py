import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_google_sheets_data(email):
    try:
        # Define the scope
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        logging.debug("Attempting to load service account credentials.")
        # Add credentials to the account
        creds = ServiceAccountCredentials.from_json_keyfile_name("relatoriosTeste.json", scope)
        logging.debug("Service account credentials loaded successfully.")

        # Authorize the client
        client = gspread.authorize(creds)
        logging.debug("Google Sheets client authorized successfully.")

        # Get the Base3 sheet
        sheet = client.open("relatorios teste").worksheet("Base3")
        logging.debug("Worksheet 'Base3' opened successfully.")

        # Get all the records of the data
        records = sheet.get_all_records()
        logging.debug(f"Fetched {len(records)} records from Google Sheets.")

        # Ensure that records are retrieved
        if not records:
            logging.debug("No records retrieved from Google Sheets.")
            return None, [], 0.0, 0.0, None

        # Filter data by email
        data = [record for record in records if record.get('e_mail_influ') == email]
        logging.debug(f"Filtered data for email {email}: {data}")

        # Ensure data is filtered correctly
        if not data:
            logging.debug(f"No data found for email: {email}")
            return None, [], 0.0, 0.0, None

        # Extract necessary fields
        influenciador = data[0].get('influenciador', 'N/A')
        picture = data[0].get('picture', '')

        # Function to safely convert currency strings to float
        def safe_convert(value):
            try:
                return float(value.replace('R$', '').replace('.', '').replace(',', '.').strip())
            except ValueError as e:
                logging.error(f"Value conversion error: {e}")
                return 0.0

        # Calculate total amounts
        total_a_receber = sum(
            safe_convert(record.get('valor_influenciador', '0'))
            for record in data if record.get('status_pgt_') == "Aguardando"
        )
        total_recebido = sum(
            safe_convert(record.get('valor_influenciador', '0'))
            for record in data if record.get('status_pgt_') == "OK"
        )

        logging.debug(f"Influenciador: {influenciador}, Total a Receber: {total_a_receber}, Total Recebido: {total_recebido}, Picture: {picture}")
        return influenciador, data, total_a_receber, total_recebido, picture

    except Exception as e:
        logging.error(f"Error fetching data from Google Sheets: {e}")
        return None, [], 0.0, 0.0, None
