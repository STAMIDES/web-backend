import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
sender_email = os.environ.get("SENDER_EMAIL")
sender_password = os.environ.get("SENDER_PASSWORD")
sender_app_password = os.environ.get("SENDER_APP_PASSWORD")

class Mailer:
    def __init__(self):
        self.sender_email = sender_email
        self.sender_app_password = sender_app_password

    def send(self, to_email, subject, body ):

        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender_email, self.sender_app_password)
                server.sendmail(sender_email, to_email, message.as_string())
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
