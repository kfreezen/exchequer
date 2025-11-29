import asyncio
from datetime import datetime
from functools import wraps
import humps
from pydantic import BaseModel

from python_api.settings import Settings


def cache(timeout=60.0):
    _values = {}
    _fetch_time = None

    def _wrapped(func):
        @wraps(func)
        def _inner(*args, **kwargs):
            key = (tuple(args), tuple(kwargs.items()))

            nonlocal _values, _fetch_time
            if (
                not _fetch_time
                or (datetime.now() - _fetch_time).total_seconds() > timeout
            ):
                _values[key] = None
            if not _values.get(key):
                _values[key] = func(*args, **kwargs)
                _fetch_time = datetime.now()

            return [
                v.model_validate(v.model_dump(mode="json", by_alias=True))
                for v in _values[key]
            ]

        return _inner

    return _wrapped


_CACHE = {}
_CACHE_FETCHING = {}
_CACHE_FETCH_TIME: dict[str, datetime] = {}


def async_cache(cache_key, timeout=60.0):
    global _CACHE, _CACHE_FETCHING, _CACHE_FETCH_TIME

    _values = _CACHE.setdefault(cache_key, {})
    _fetching = _CACHE_FETCHING.setdefault(cache_key, {})
    _fetching = {}  # Harhar this is rather fetching

    def _wrapped(func):
        @wraps(func)
        async def _inner(*args, **kwargs):
            key = (tuple(args[1:]), tuple(kwargs.items()))

            nonlocal _values
            cache_fetch_time = _CACHE_FETCH_TIME.get(cache_key)
            if (
                not cache_fetch_time
                or (datetime.now() - cache_fetch_time).total_seconds() > timeout
            ):
                print("Fetching because expiration")
                _fetching[key] = True
                _values[key] = await func(*args, **kwargs)
                _CACHE_FETCH_TIME[cache_key] = datetime.now()
                _fetching[key] = False
            elif not _values.get(key) and _fetching.get(key, False):
                print("Waiting")
                while _fetching.get(key, False):
                    await asyncio.sleep(0.1)
            elif not _values.get(key):
                print("Fetching because not there", key)
                _fetching[key] = True
                _values[key] = await func(*args, **kwargs)
                _CACHE_FETCH_TIME[cache_key] = datetime.now()
                _fetching[key] = False

            if _values[key] is None:
                return None

            if isinstance(_values[key], BaseModel):
                v = _values[key]
                return v.model_validate(v.model_dump(mode="json", by_alias=True))
            else:
                return [
                    v.model_validate(v.model_dump(mode="json", by_alias=True))
                    for v in _values[key]
                ]

        return _inner

    return _wrapped


def compatibility_please(func):
    @wraps(func)
    async def _inner(self, *args, **kwargs):
        args = list(args)
        for i, arg in enumerate(args):
            args[i] = self._compat("from_user", arg)

        for key, value in kwargs.items():
            kwargs[key] = self._compat("from_user", value)

        return self._compat("to_user", await func(self, *args, **kwargs))

    return _inner


class Repository:
    def _compat(self, fn_name, obj):
        if isinstance(obj, list):
            return [self._compat(fn_name, item) for item in obj]
        if fn := getattr(obj, fn_name, None):
            res = fn(self.app_platform, self.app_build)
            return res or obj
        return obj

    def __init__(self, app_platform, app_build):
        self.app_platform = app_platform
        try:
            self.app_build = int(app_build) if app_build else None
        except ValueError:
            self.app_build = None

    def _sort_keys(self, sort: str | None, allowed: dict | None = None):
        allowed = allowed or {}

        sort_list = sort.split(",") if sort else []
        sort_list = [s.split(" ") for s in sort_list] if sort_list else []
        for s in sort_list:
            if len(s) > 1:
                s[1] = "ASC" if s[1] == "asc" else "DESC"
            else:
                s.append("ASC")

            s[0] = humps.decamelize(s[0])

        sort_list = sort_list or []
        return {allowed[s[0]]: s[1] for s in sort_list if s[0] in allowed}
