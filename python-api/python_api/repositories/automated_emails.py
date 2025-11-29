from datetime import datetime
import json
from python_api.repositories.users import UserRepository
from python_api.settings import Settings
from python_api.models.emails import AutomatedEmail, EmailType


class AutomatedEmails:
    def __init__(self, settings: Settings, db):
        self.db = db
        self.environment = settings.environment

    async def cancel(self, user_id: str, email_type: EmailType, template: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM automated_emails
                WHERE user_id = %s 
                AND email_type = %s 
                AND sent_at IS NULL
                AND template = %s
                """,
                (user_id, email_type, template),
            )

    async def get_due_emails(self) -> list[AutomatedEmail]:
        sql = """
        SELECT
        e.id, e.user_id, u.email AS user_email, u.roles, e.email_type,
        e.subject, e.variables, e.scheduled_at, e.sent_at, e.template
        FROM automated_emails e
        JOIN users u ON e.user_id = u.id
        WHERE sent_at IS NULL AND scheduled_at < EXTRACT(EPOCH FROM NOW())
        AND scheduled_at > EXTRACT(EPOCH FROM NOW() - INTERVAL '1 hour')
        """

        async with self.db.cursor() as cur:
            await cur.execute(sql)
            emails = await cur.fetchall()
            if self.environment != "production":
                emails = [e for e in emails if "admin" in e["roles"]]
            return [AutomatedEmail.model_validate(email) for email in emails]

    async def mark_sent(self, email_id: int):
        async with self.db.cursor() as cur:
            await cur.execute(
                "UPDATE automated_emails SET sent_at = EXTRACT(EPOCH FROM NOW()) WHERE id = %(email_id)s",
                {"email_id": email_id},
            )

    async def schedule(
        self,
        automated_email: AutomatedEmail,
    ):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO automated_emails
                (user_id, email_type, subject, variables, scheduled_at, template)
                VALUES
                (%(user_id)s, %(email_type)s, %(subject)s, %(variables)s, %(scheduled_at)s, %(template)s)
                RETURNING id
                """,
                {
                    "user_id": automated_email.user_id,
                    "email_type": automated_email.email_type,
                    "subject": automated_email.subject,
                    "variables": json.dumps(automated_email.variables),
                    "scheduled_at": automated_email.scheduled_at,
                    "template": automated_email.template,
                },
            )

            email_id = await cur.fetchone()
            return email_id
