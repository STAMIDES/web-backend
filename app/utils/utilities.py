import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sender_email = "midesmailsender@gmail.com"
sender_password = "asjd312dsajnzxASD1112"

class Mailer:
    def __init__(self):
        self.sender_email = sender_email
        self.sender_password = sender_password

def send(self, to_email, subject, body ):

    message = MIMEMultipart()
    message["From"] = self.sender_email
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(self.sender_email, self.sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
