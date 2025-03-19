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

    def send_forgot_password_email(self, to_email: str, user_name: str, reset_link: str):
        """
        Sends a forgot password email to the user with a reset link
        
        Args:
            to_email (str): The recipient's email address
            user_name (str): The user's name (or 'usuario' if not available)
            reset_link (str): The password reset link
        """
        subject = "Restablecer contraseña"
        body = f"""Hola {user_name},

Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para crear una nueva contraseña:

{reset_link}

Este enlace expirará en 24 horas.

Si no solicitaste este cambio, puedes ignorar este correo.

Saludos,
El equipo de MIDES"""

        self.send(to_email, subject, body)
