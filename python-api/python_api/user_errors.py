from datetime import datetime
import json
from logging import ERROR
from typing import Any
from fastapi.encoders import jsonable_encoder


class UserErrors:
    def __init__(self, db):
        self.db = db
        self.errors = []

    def error(
        self,
        type: str,
        user_id,
        endpoint=None,
        status_code=None,
        details=None,
        **others,
    ):
        self.log(ERROR, type, user_id, endpoint, status_code, details, **others)

    def log(
        self,
        severity: int,
        type: str,
        user_id: str | None = None,
        endpoint: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
        **others,
    ):
        details = details or {}
        self.errors.append(
            jsonable_encoder(
                {
                    "user_id": user_id,
                    "severity": severity,
                    "type": type,
                    "created_at": datetime.now(),
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "details": json.dumps(jsonable_encoder({**details, **others})),
                }
            ),
        )

    async def submit_all(self):
        if self.errors:
            try:
                async with self.db.cursor() as cur:
                    await cur.executemany(
                        """
                        INSERT INTO error_log
                        (user_id, severity, type, created_at, endpoint, status_code, details)
                        VALUES
                        (
                        %(user_id)s,
                        %(severity)s,
                        %(type)s,
                        %(created_at)s,
                        %(endpoint)s,
                        %(status_code)s,
                        %(details)s
                        )
                        """,
                        self.errors,
                    )
            except Exception as e:
                print(e)
                for error in self.errors:
                    print(f"[[error]]:{error}")
