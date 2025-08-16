# app/emailer.py
import os
import smtplib
from email.message import EmailMessage


class Emailer:
    def __init__(self):
        # Read email + password from environment variables
        self.email = os.getenv("EMAIL_ADDRESS")
        self.password = os.getenv("EMAIL_PASSWORD")

        if not self.email or not self.password:
            raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set as environment variables")

    def send(self, recipient, subject, body, attachments=None):
        msg = EmailMessage()
        msg['From'] = self.email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.set_content(body)

        if attachments:
            for attachment in attachments:
                with open(attachment, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(f.name)
                msg.add_attachment(
                    file_data,
                    maintype='application',
                    subtype='octet-stream',
                    filename=file_name
                )

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(self.email, self.password)
            smtp_server.send_message(msg)


class SendEmail:
    def __init__(self, email, subject, body, attachments=None):
        self.emailer = Emailer()
        self.receiver = email
        self.subject = subject
        self.body = body
        self.attachments = attachments

    def sendMessage(self):
        self.emailer.send(self.receiver, self.subject, self.body, self.attachments)
