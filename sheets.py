import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name("path/to/your/credentials.json", scope)

# Authorize the clientsheet 
client = gspread.authorize(creds)

# Get the sheet
sheet = client.open("your_google_sheet_name").sheet1

# Get all the records of the data
data = sheet.get_all_records()

print(data)
