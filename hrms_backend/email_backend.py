import ssl
import smtplib

from django.core.mail.backends.smtp import EmailBackend


class CustomEmailBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False

        self.connection = smtplib.SMTP(self.host, self.port)

        self.connection.ehlo()

        context = ssl._create_unverified_context()

        self.connection.starttls(context=context)

        self.connection.ehlo()

        self.connection.login(
            self.username,
            self.password
        )

        return True