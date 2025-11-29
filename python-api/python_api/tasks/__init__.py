import json
from datetime import datetime

from celery import Celery

import asyncio
from functools import wraps
from psycopg.connection_async import AsyncConnection as AsyncConnectionGeneric
from psycopg.rows import DictRow

from python_api.settings import Settings
from fastapi.encoders import jsonable_encoder

from python_api.task_deps import async_conn

from python_api.task_deps import (
    redis_dep,
    automated_emails_dep,
    mailer_dep,
    email_generator_dep,
)

AsyncConnection = AsyncConnectionGeneric[DictRow]


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


settings = Settings()
app = Celery("python_api_tasks", broker=settings.redis_url)


@app.task
@coro
async def send_emails():
    print("Sending emails  =============================")
    async with async_conn() as conn:
        automated_email_repo = await automated_emails_dep(conn)
        mailer = await mailer_dep()
        email_gen = await email_generator_dep()

        emails = await automated_email_repo.get_due_emails()

        start_time = datetime.now().timestamp()
        total_sent = 0
        for email in emails:
            if not email.id:
                continue

            subject, text, html = email_gen.generate_email(
                email.subject,
                email.template,
                **email.variables if email.variables else {},
            )

            if email.user_email:
                mailer.sendmail(email.user_email, subject, text, html)

            await automated_email_repo.mark_sent(email.id)

            total_sent += 1

        end_time = datetime.now().timestamp()
        emails_per_second = total_sent / (end_time - start_time)
        print(
            f"Sent {total_sent} emails in {end_time - start_time} seconds ({emails_per_second} emails per second)"
        )


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    _ = kwargs  # Unused, but required by Celery

    sender.add_periodic_task(60, send_emails.s())
