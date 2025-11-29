from python_api.models.users import UUIDString, User
from python_api.models import CamelModel


KEYS = [
    "lastPdfTime",
    "lastPdfKey",
    "currentSlowdown",
    "currentSlowdownThreshold",
    "avgPdfTime",
    "pdfCount",
    "banPdfDownloads",
    "violations",
]


class PDFAbuseMetrics(CamelModel):
    last_pdf_time: float | None = None
    last_pdf_key: str | None = None
    current_slowdown: float | None = None
    current_threshold: float | None = None
    avg_pdf_time: float | None = None
    pdf_count: int | None = None
    ban_pdf_downloads: int | None = None
    violations: int | None = None


class PDFAbuseUser(User):
    pdf_abuse_metrics: PDFAbuseMetrics | None = None


class AbuseRepository:
    def __init__(self, redis, users):
        self.users = users
        self.redis = redis

    async def get_user(self, user_id: UUIDString) -> PDFAbuseUser | None:
        user = await self.users.get_user(user_id)
        if not user:
            return None

        keys = [f"pdf_slowdown:{user.id}:{key}" for key in KEYS]
        abuser_metrics = await self.redis.mget(keys)

        return PDFAbuseUser(
            **user.model_dump(mode="json", by_alias=True),
            pdf_abuse_metrics=PDFAbuseMetrics(
                **{
                    "lastPdfTime": float(abuser_metrics[0] or 0),
                    "lastPdfKey": (
                        abuser_metrics[1].decode() if abuser_metrics[1] else None
                    ),
                    "currentSlowdown": float(abuser_metrics[2] or 0),
                    "currentThreshold": float(abuser_metrics[3] or 0),
                    "avgPdfTime": float(abuser_metrics[4] or 0),
                    "pdfCount": int(abuser_metrics[5] or 0),
                    "banPdfDownloads": int(abuser_metrics[6] or 0),
                    "violations": int(abuser_metrics[7] or 0),
                }
            ),
        )

    async def get_users(self, include_all_users: bool = False):
        abusers = await self.redis.smembers("pdf_slowdown:users")
        abuser_ids = list([a.decode() for a in abusers])

        abuser_users = [await self.users.get_user(user_id) for user_id in abuser_ids]
        abuser_users = [user for user in abuser_users if user is not None]

        pipe = self.redis.pipeline()
        for abuser in abuser_users:
            keys = [f"pdf_slowdown:{abuser.id}:{key}" for key in KEYS]
            pipe.mget(keys)

        abuser_metrics = await pipe.execute()
        final_list = [
            PDFAbuseUser(
                **abuser.model_dump(mode="json", by_alias=True),
                pdf_abuse_metrics=PDFAbuseMetrics(
                    **{
                        "lastPdfTime": float(abuser_metrics[i][0] or 0),
                        "lastPdfKey": (
                            abuser_metrics[i][1].decode()
                            if abuser_metrics[i][1]
                            else None
                        ),
                        "currentSlowdown": float(abuser_metrics[i][2] or 0),
                        "currentThreshold": float(abuser_metrics[i][3] or 0),
                        "avgPdfTime": float(abuser_metrics[i][4] or 0),
                        "pdfCount": int(abuser_metrics[i][5] or 0),
                        "banPdfDownloads": int(abuser_metrics[i][6] or 0),
                        "violations": int(abuser_metrics[i][7] or 0),
                    }
                ),
            )
            for i, abuser in enumerate(abuser_users)
            if float(abuser_metrics[i][2] or 0) > 0
            or (include_all_users and (abuser_metrics[i][5] or 0) > 0)
        ]
        return final_list

    async def delete_pdf_abuser(self, user_id: str):
        user = await self.users.get_user(user_id)
        if not user:
            return False

        keys = [f"pdf_slowdown:{user.id}:{key}" for key in KEYS]
        del keys[-1]  # don't remove violation count

        await self.redis.delete(*keys)
        await self.redis.srem("pdf_slowdown:users", user.id)
        return True
