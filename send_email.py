import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()


def send_email(subject: str, body: str, to_email: str = None):
    sender_email = os.getenv('EMAIL_ADDRESS')
    app_password = os.getenv('EMAIL_APP_PASSWORD')

    if not sender_email or not app_password:
        print("❌ EMAIL_ADDRESS or EMAIL_APP_PASSWORD not set in .env")
        return False

    recipient = to_email or sender_email

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()
        print(f"✅ Email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
