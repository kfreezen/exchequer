import click
import csv
from python_api.mail import EmailGenerator, Mailer

from python_api.settings import Settings


@click.command()
@click.option("email_list", "--email")
@click.argument("html_file")
def whoops(email_list, html_file):
    settings = Settings()

    mailer = Mailer(settings)
    generator = EmailGenerator(settings)

    with open(email_list, "r") as f:
        emails = f.readlines()

    with open(html_file, "r") as htmlf:
        html_message = htmlf.read()

    for email in emails:
        subject, text, html = generator.generate_email(
            "Whoops!", "whoops", email=email, message=html_message
        )
        mailer.sendmail(email, subject, text, html=html)
        print(f"Sent whoops email to {email}")
