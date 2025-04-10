import os
import json
import base64
from flask import Flask, render_template
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
import random

app = Flask(__name__)

# Google Sheets setup
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
client = None  # Initialize client outside the if block
sheet = None  # Initialize sheet outside the if block
sheet_id= os.environ.get("SHEET_ID")
encoded_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON_BASE64")

if encoded_creds:
    try:
        decoded_creds = base64.b64decode(encoded_creds).decode()
        creds_info = json.loads(decoded_creds)
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).sheet1
    except Exception as e:
        print(f"Error initializing Google Sheets: {e}")

# Email setup (using Gmail as an example)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS= os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD= os.environ.get("EMAIL_PASSWORD")
def send_email(to_email, name):
    messages = [
        f"Your registration was successful! Welcome aboard, {name}!",
        f"Great news, {name}! Your registration is complete!",
        f"Success! You've been registered, {name}. Get ready to start!",
        f"Registration confirmed, {name}! We're excited to have you!"
    ]
    random_message = random.choice(messages)

    subject = "Registration Successful"
    body = f"Dear {name},\n\n{random_message}\n\nBest regards,\nYour Team"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return True  # Email sent successfully
    except Exception as e:
        print(f"Error sending email: {e}")
        return False  # Email sending failed

def check_new_submission():
    if not client or not sheet:
        return "Google Sheets credentials or sheet not loaded."  # Handle the case where Google Sheets is not initialized

    try:
        with open("last_row.txt", "r") as f:
            last_row = int(f.read().strip())
    except FileNotFoundError:
        last_row = 1

    try:
        total_rows = len(sheet.get_all_values())
        if total_rows > last_row:
            row_data = sheet.row_values(total_rows)
            email = row_data[1]
            name = row_data[2]
            email_sent = send_email(email, name)

            with open("last_row.txt", "w") as f:
                f.write(str(total_rows))
            if email_sent:
                return f"Email sent to {email}"
            else:
                return f"Failed to send email to {email}"
        else:
            return "No new submissions"
    except Exception as e:
        return f"Error accessing Google Sheet: {e}"

@app.route("/")
def index():
    message = check_new_submission()
    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)