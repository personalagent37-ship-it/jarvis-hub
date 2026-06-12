import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def send_email(to: str, subject: str, body: str) -> str:
    """Send an email using SMTP."""
    try:
        email_address = os.environ.get("SMTP_USER", "codingpython57@gmail.com")
        email_password = os.environ.get("SMTP_PASS", "").replace(" ", "")
        
        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_address, email_password)
        server.send_message(msg)
        server.quit()

        return f"✅ Email sent to {to} successfully!"
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"
