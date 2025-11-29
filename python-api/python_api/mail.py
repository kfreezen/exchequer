from email.message import Message
from smtplib import SMTP
import smtplib
from python_api.settings import Settings
from boto3 import client
from jinja2 import Environment, FileSystemLoader


class Mailer:
    def __init__(self, settings: Settings) -> None:
        self.ses = client(
            "ses",
            region_name=settings.ses_region,
            aws_access_key_id=settings.ses_api_key,
            aws_secret_access_key=settings.ses_api_secret,
        )

        self.source_email = settings.smtp_email
        self.friendly_from = settings.friendly_from

    def sendmail(self, to: str, subject: str, mail: str, html: str | None = None):
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


class EmailGenerator:
    def __init__(self, settings):
        self.loader = FileSystemLoader("templates/")
        self.env = Environment(loader=self.loader, cache_size=0)
        self.tagline = settings.email_tagline

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
