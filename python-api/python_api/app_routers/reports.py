from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from fastapi import APIRouter, Query

import jinja2
from python_api.dependencies import AsyncPostgresDep, ValidJWTDep
from python_api.models import CamelModel, UUIDString

router = APIRouter(prefix="/reports", tags=["reports"])


class ProfitAndLossItem(CamelModel):
    envelope_id: UUIDString
    entity_id: UUIDString
    entity_name: str
    entity_type: str
    envelope_name: str
    amount: Decimal


class ReportAliasUpdateRequest(CamelModel):
    alias: str


@router.put("/aliases/{report_type}/{envelope_id}")
async def update_report_alias(
    report_type: str,
    envelope_id: UUIDString,
    body: ReportAliasUpdateRequest,
    db: AsyncPostgresDep,
    valid_jwt: ValidJWTDep,
):
    async with db.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO report_envelope_aliases (id, user_id, report_type, envelope_id, alias)
            VALUES (%(id)s, %(user_id)s, %(report_type)s, %(envelope_id)s, %(alias)s)
            ON CONFLICT (user_id, report_type, envelope_id)
            DO UPDATE SET alias = EXCLUDED.alias;
            """,
            {
                "id": uuid4(),
                "user_id": valid_jwt["sub"],
                "report_type": report_type,
                "envelope_id": envelope_id,
                "alias": body.alias,
            },
        )
    return {"status": "success"}


@router.get("/profit-and-loss")
async def get_profit_and_loss_report(
    db: AsyncPostgresDep,
    valid_jwt: ValidJWTDep,
    start_date: datetime = Query(alias="startDate"),
    end_date: datetime | None = Query(None, alias="endDate"),
):
    end_date = end_date or datetime.now()

    query = """
SELECT e.id as envelope_id, et.id as entity_id, et.name as entity_name, et.type as entity_type, COALESCE(rea.alias, e.name) as envelope_name, SUM(t.amount) as amount
FROM envelopes e
LEFT JOIN report_envelope_aliases rea ON rea.envelope_id = e.id AND rea.user_id = e.user_id AND rea.report_type = 'profit-and-loss'
INNER JOIN transactions t ON t.envelope_id = e.id
INNER JOIN entities et ON et.id = t.entity_id
WHERE e.user_id = %(user_id)s AND
et.type = 'business' AND
t.date >= %(start_date)s AND t.date <= %(end_date)s
GROUP BY e.id, et.id, et.name, et.type, e.name, rea.alias
ORDER BY et.name, e.name;
    """

    async with db.cursor() as cursor:
        await cursor.execute(
            query,
            {
                "start_date": start_date,
                "end_date": end_date,
                "user_id": valid_jwt["sub"],
            },
        )
        results = await cursor.fetchall()

    return [ProfitAndLossItem.model_validate(row) for row in results]


@router.get("/profit-and-loss/html")
async def get_profit_and_loss_report_html(
    db: AsyncPostgresDep,
    valid_jwt: ValidJWTDep,
    start_date: datetime = Query(alias="startDate"),
    end_date: datetime | None = Query(None, alias="endDate"),
    envelopes: str | None = None,
):
    envelopes = envelopes or ""

    end_date = end_date or datetime.now()

    envelope_ids: list[int] = [int(env.strip()) for env in envelopes.split(",")]

    query = """
SELECT e.id as envelope_id, et.id as entity_id, et.name as entity_name, et.type as entity_type, COALESCE(rea.alias, e.name) as envelope_name, SUM(t.amount) as amount
FROM envelopes e
LEFT JOIN report_envelope_aliases rea ON rea.envelope_id = e.id AND rea.user_id = e.user_id AND rea.report_type = 'profit-and-loss'
INNER JOIN transactions t ON t.envelope_id = e.id
INNER JOIN entities et ON et.id = t.entity_id
WHERE e.user_id = %(user_id)s AND
et.type = 'business' AND
t.date >= %(start_date)s AND t.date <= %(end_date)s
AND (%(envelopes)s IS NULL OR e.id = ANY(%(envelopes)s))
GROUP BY e.id, et.id, et.name, et.type, e.name, rea.alias
ORDER BY et.name, e.name;
    """

    async with db.cursor() as cursor:
        await cursor.execute(
            query,
            {
                "start_date": start_date,
                "end_date": end_date,
                "user_id": valid_jwt["sub"],
                "envelopes": envelope_ids or None,
            },
        )
        results = await cursor.fetchall()
