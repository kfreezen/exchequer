from email.message import Message
from smtplib import SMTP, SMTP_SSL
from python_api.settings import Settings
from boto3 import client
from jinja2 import Environment, FileSystemLoader
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Mailer:
    def __init__(self, settings: Settings) -> None:
        if settings.ses_api_key:
            self.ses = client(
                "ses",
                region_name=settings.ses_region,
                aws_access_key_id=settings.ses_api_key,
                aws_secret_access_key=settings.ses_api_secret,
            )
            self.smtp = None
        else:
            self.ses = None
            self.smtp = SMTP(settings.smtp_hostname, 587, timeout=10)
            self.smtp.starttls()
            self.smtp.login(settings.smtp_username, settings.smtp_password)

        self.source_email = settings.smtp_email
        self.friendly_from = settings.friendly_from

    def sendmail_ses(self, to: str, subject: str, mail: str, html: str | None = None):
        if self.ses:
            body = {
                "Text": {
                    "Data": mail,
                },
            }

            if html:
                body["Html"] = {
                    "Data": html,
                }

            response = self.ses.send_email(
                Source=f"{self.friendly_from} <{self.source_email}>",
                Destination={
                    "ToAddresses": [to],
                },
                Message={
                    "Subject": {
                        "Data": subject,
                    },
                    "Body": body,
                },
            )

            return response.get("MessageId")

    def sendmail(self, to: str, subject: str, mail: str, html: str | None = None):
        if self.ses:
            return self.sendmail_ses(to, subject, mail, html)

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.friendly_from} <{self.source_email}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(mail, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))

        if self.smtp:
            self.smtp.sendmail(self.source_email, to, msg.as_string())


class EmailGenerator:
    def __init__(self, settings):
        self.loader = FileSystemLoader("templates/")
        self.env = Environment(loader=self.loader, cache_size=0)
        self.tagline = "Cleffy Music"

        self.env.globals["tagline"] = self.tagline
        self.env.globals["app_url"] = settings.base_app_url

    def generate_password_reset(self, reset_code):
        return self.generate_email(
            "Password Reset", "password_reset", resetCode=reset_code
        )

    def generate_email(self, subject, template, **variables):
        html_template = self.env.get_template(f"{template}.html")
        text_template = self.env.get_template(f"{template}.txt")

        html = html_template.render(**variables)
        text = text_template.render(**variables)

        return subject, text, html
