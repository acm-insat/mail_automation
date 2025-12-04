from __future__ import print_function
import base64
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime

# ----------------------------- CONFIG -----------------------------
# Put your Google Sheet ID here
SPREADSHEET_ID = "1I2L48ejaRmL1dDm7JmIjv_CX5lqIwjHmMnIJQlIQtw8"

# Gmail & Sheets API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Path to your email signature image
SIGNATURE_IMAGE = "signature_mail_rh.png"

# Feedback form link
FORM_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSexGv_oQi77lppRIEsV6HENuItai31x3UYQFskV2JTQrYqB7Q/viewform?usp=publish-editor"

# --------------------------- AUTH FUNCTIONS ---------------------------
def authenticate_google_services():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    gmail_service = build("gmail", "v1", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)
    return gmail_service, sheets_service

# --------------------------- SHEETS HELPERS ---------------------------
def normalize_header(h):
    return h.strip().replace(" ", "").lower()

def load_sheet_data(sheets_service, tab_name):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{tab_name}!A:Z"
    ).execute()
    values = result.get("values", [])
    if not values:
        return [], [], []
    headers_raw = values[0]
    headers = [normalize_header(h) for h in headers_raw]
    data_rows = values[1:]
    return headers, data_rows, headers_raw

def get_col_idx(headers, col_name):
    norm = normalize_header(col_name)
    if norm not in headers:
        raise Exception(f"Missing required column: {col_name}")
    return headers.index(norm)

def update_sheet_cell(sheets_service, tab_name, row, col, value):
    range_name = f"{tab_name}!{chr(65 + col)}{row}"
    body = {"values": [[value]]}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=body
    ).execute()

# --------------------------- EMAIL FUNCTIONS ---------------------------
def build_html_email(name, cert_link):
    return f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
  <p>Hi {name},</p>
  <p>Thank you for being part of CodeQuest 3.0, a beginner-friendly adventure where curiosity,
     courage, and a little competitive chaos create magic.</p>
  <p>You’ve completed this edition, and we’re happy to award you your official participation certificate.</p>
  <p><strong>Certificate:</strong><br>
     <a href="{cert_link}" target="_blank">{cert_link}</a></p>
  <p>We hope this experience helped you learn, grow, and feel more confident in competitive programming.
     Every explorer starts somewhere — today, you took a step forward.</p>
  <p><strong>Feedback Form:</strong><br>
     <a href="{FORM_LINK}" target="_blank">{FORM_LINK}</a></p>
  <p>Once again, congratulations and thank you for journeying down the rabbit hole with us.<br>
     We look forward to your participation in WinterCup.</p>
  <p>The CodeQuest Team</p>
  <img src="{signature_mail_rh.png}" style="margin-top:20px; width:100%; max-width:500px;">
</body>
</html>
"""

def send_email(gmail_service, recipient, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail_service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

# --------------------------- MAIN ---------------------------
def main():
    gmail, sheets = authenticate_google_services()

    tab_name = "Recipients"
    headers, rows, _ = load_sheet_data(sheets, tab_name)

    email_col = get_col_idx(headers, "email")
    name_col = get_col_idx(headers, "name")
    cert_col = get_col_idx(headers, "certiflink")
    sent_col = get_col_idx(headers, "sent?")
    timestamp_col = get_col_idx(headers, "timestamp")

    for i, row in enumerate(rows, start=2):
        email = row[email_col].strip()
        name = row[name_col].strip()
        cert_link = row[cert_col].strip()
        sent_status = row[sent_col].strip().lower() if len(row) > sent_col else ""

        if sent_status == "yes":
            continue

        html_body = build_html_email(name, cert_link)
        try:
            send_email(gmail, email, "Your CodeQuest 3.0 Certificate is Here!", html_body)
            update_sheet_cell(sheets, tab_name, i, sent_col, "Yes")
            update_sheet_cell(sheets, tab_name, i, timestamp_col, datetime.now().strftime("%Y-%m-%d %H:%M"))
            print(f"Sent email to {email}")
        except Exception as e:
            print(f"Error sending to {email}: {e}")

        time.sleep(0.5)

    print("All done.")

if __name__ == "__main__":
    main()
