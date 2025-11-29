from datetime import datetime
import click
import asyncio
import json

from psycopg.rows import dict_row

from redis.asyncio import Redis
from python_api.mail import Mailer, EmailGenerator
from python_api.models.emails import EmailType, AutomatedEmail

from python_api.repositories.users import UserRepository
from python_api.repositories.automated_emails import AutomatedEmails

from python_api.settings import Settings
from python_api.db_conn import AsyncConnection
from python_api import tasks


@click.command()
@click.argument("email_type")
@click.argument("template")
@click.argument("subject")
@click.argument("send_at")
@click.option("--custom-variables", default={})
def schedule_email(
    email_type: str, template: str, subject: str, send_at: int, custom_variables: str
):
    async def _schedule_email():
        settings = Settings()
        db = await AsyncConnection.connect(settings.database_dsn, row_factory=dict_row)
        user_repo = UserRepository(None, None, db, settings)
        automated_email_repo = AutomatedEmails(settings, db)

        users = await user_repo.get_subscribed_users(EmailType(email_type))

        for user in users:
            variables = {
                "name": user.name,
                "email_id": user.email_id,
            }

            variables.update(json.loads(custom_variables))

            await automated_email_repo.schedule(
                AutomatedEmail(
                    user_id=user.id,
                    email_type=EmailType(email_type),
                    subject=subject,
                    template=template,
                    variables=variables,
                    scheduled_at=send_at,
                )
            )

        await db.commit()

    asyncio.run(_schedule_email())


# If you just run test-scheduled-emails, it send all scheduled emails
@click.command()
@click.argument("user_id", default="")
@click.argument("email_type", default="")
@click.argument("template", default="")
@click.argument("subject", default="")
@click.option("--custom-variables", default={})
@click.option("--only-create", is_flag=True, default=False)
@click.option("--count", default=1)
def test_scheduled_emails(
    user_id: str,
    email_type: str,
    template: str,
    subject: str,
    custom_variables: str,
    only_create: bool,
    count: int,
):
    async def _test_scheduled_emails():
        settings = Settings()
        db = await AsyncConnection.connect(
            settings.database_dsn, row_factory=dict_row, autocommit=True
        )
        user_repo = UserRepository(None, None, db, settings)
        automated_email_repo = AutomatedEmails(settings, db)
        mailer = Mailer(settings)
        email_gen = EmailGenerator(settings)

        if user_id:
            user = await user_repo.get_user(user_id)
            if not user:
                print(f"User with ID {user_id} not found")
                return

            variables = {
                "name": user.name,
                "email_id": user.email_id,
            }

            variables.update(json.loads(custom_variables))

            for i in range(count):
                variables["i"] = i
                await automated_email_repo.schedule(
                    AutomatedEmail(
                        user_id=user_id,  # pyright: ignore
                        email_type=EmailType(email_type),
                        subject=subject,
                        template=template,
                        variables=variables,
                        scheduled_at=int(datetime.now().timestamp()),
                    )
                )
        if not only_create:
            start_time = datetime.now().timestamp()
            total_sent = 0
            emails = await automated_email_repo.get_due_emails()
            for email in emails:
                _subject, text, html = email_gen.generate_email(
                    email.subject, email.template, **(email.variables or {})
                )

                if email.user_email and email.id:
                    mailer.sendmail(email.user_email, _subject, text, html)
                    await automated_email_repo.mark_sent(email.id)

                total_sent += 1

            end_time = datetime.now().timestamp()
            emails_per_second = total_sent / (end_time - start_time)
            print(
                f"Sent {total_sent} emails in {end_time - start_time} seconds ({emails_per_second} emails per second)"
            )

    asyncio.run(_test_scheduled_emails())


@click.command()
def init_subscriptions():
    async def _init_subscriptions():
        settings = Settings()
        db = await AsyncConnection.connect(settings.database_dsn, row_factory=dict_row)
        user_repo = UserRepository(None, None, db, settings)

        users, _ = await user_repo.get_users()

        for user in users:
            await user_repo.subscribe_user(str(user.id), EmailType.PROMOTIONAL)
            await user_repo.subscribe_user(str(user.id), EmailType.TRANSACTIONAL)
        await db.commit()

    asyncio.run(_init_subscriptions())
