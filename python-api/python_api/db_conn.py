from collections.abc import AsyncGenerator
from psycopg import AsyncConnection as AsyncConnectionGeneric, AsyncCursor
from psycopg.rows import DictRow
import psycopg_pool
from psycopg_pool import AsyncConnectionPool
from contextlib import asynccontextmanager


CONN_REF_COUNT = 0

AsyncConnection = AsyncConnectionGeneric[DictRow]


class LazyConnectionContextManagerAsync:
    def __init__(
        self, conn_pool: AsyncConnectionPool[AsyncConnection], jwt: dict | None
    ):
        self.conn_pool = conn_pool
        self.conn: AsyncConnection | None = None
        self._jwt = jwt

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        global CONN_REF_COUNT

        if self.conn is not None:
            CONN_REF_COUNT -= 1
            await self.conn.commit()  # Prevent rollback notifications
            await self.conn_pool.putconn(self.conn)
            self.conn = None

    async def rollback(self):
        if self.conn is not None:
            await self.conn.rollback()

    @asynccontextmanager
    async def cursor(
        self, *args, **kwargs
    ) -> AsyncGenerator[AsyncCursor[DictRow], None]:
        global CONN_REF_COUNT
        if self.conn is None:
            try:
                self.conn = await self.conn_pool.getconn()
                if self._jwt is not None:
                    async with self.conn.cursor() as cursor:
                        await self.conn.execute(
                            "SELECT set_config('app.current_user_id', %s, true);",
                            (self._jwt.get("sub"),),
                        )
                CONN_REF_COUNT += 1
            except psycopg_pool.PoolTimeout:
                print("Pool timeout:", self.conn_pool.get_stats())

        if self.conn is None:
            raise RuntimeError("Connection is not available")

        async with self.conn.cursor(*args, **kwargs) as cursor:
            yield cursor
