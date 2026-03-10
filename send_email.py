import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()


def send_email(subject: str, body: str, to_emails=None, to_email=None):
    sender_email = os.getenv('EMAIL_ADDRESS')
    app_password = os.getenv('EMAIL_APP_PASSWORD')

    if not sender_email or not app_password:
        print("EMAIL_ADDRESS or EMAIL_APP_PASSWORD not set in .env")
        return False

    # Backward-compatible alias support: to_email -> to_emails
    recipients_input = to_emails if to_emails is not None else to_email

    if recipients_input is None:
        recipients = [sender_email]
    elif isinstance(recipients_input, str):
        # Allow comma-separated string input
        recipients = [email.strip() for email in recipients_input.split(',') if email.strip()]
    else:
        recipients = [email.strip() for email in recipients_input if isinstance(email, str) and email.strip()]

    if not recipients:
        print("No valid recipient emails provided")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {', '.join(recipients)}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
