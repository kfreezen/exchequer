import asyncio
import secrets
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, Header, Request, Response, status
import fastapi
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from httpx import HTTPStatusError
from passlib.exc import PasswordSizeError, UnknownHashError

import time
from datetime import datetime, timedelta, timezone, UTC
from python_api.models import CamelModel
from python_api.models.users import (
    DbUser,
    SsoUser,
    DbUserToken,
    UserRole,
)
from python_api.settings import Settings
from python_api.sso import InvalidIDToken

from python_api.sso.apple import AppleSSORequest

from python_api import dependencies

from python_api.routers import (
    dashboard,
    users,
    admin_router,
)
from python_api.app_routers import app_router, users as app_router_users

from python_api.utils import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token_from_user,
    get_jwks,
)
import sentry_sdk

settings = Settings()

logging.basicConfig(level=settings.log_level, force=True)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=3)

if settings.sentry_dsn:
    print("Sentry DSN found, initializing sentry")
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        environment=settings.environment,
    )
else:
    print("No sentry DSN found, skipping sentry initialization")


USER_ROLES = [UserRole[r] for r in UserRole.__members__]

origins = [
    "https://admin.exchequer.io",
    "https://exchequer.io",
    "http://localhost:3040",
    "http://localhost:8040",
    "http://localhost:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""Profile the current request

Taken from https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
with small improvements.

"""


@app.get("/test", include_in_schema=False)
async def test():
    return {"message": "Hello World2!"}


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(admin=Depends(dependencies.admin)):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Exchequer API",
    )


@app.get("/openapi.json", include_in_schema=False)
async def openapi(admin=Depends(dependencies.admin)):
    return get_openapi(title="Exchequer API", version="0.0.1", routes=app.routes)


@app.get("/.well-known/keys")
async def get_keys(settings: dependencies.SettingsDep):
    return get_jwks(settings)


async def _create_refresh_token(users, refresh_token, user_id):
    token = DbUserToken(
        id=refresh_token,
        date=int(datetime.now().timestamp()),
        refresh_token=refresh_token,
        provider="apple",
        user_id=user_id,
        last_used=int(datetime.now().timestamp()),
    )
    await users.insert_refresh_token(token)


class GoogleSSORequest(CamelModel):
    name: str | None = None
    email: str | None = None
    server_auth_code: str | None = None
    id_token: str
    user_id: str | None = None


@app.get("/test-email/{template}", include_in_schema=False)
async def test_email(
    template: str,
    req: Request,
    email_gen: dependencies.EmailGeneratorDep,
    mailer: dependencies.MailerDep,
    admin=Depends(dependencies.admin),
):
    subject, text, html = email_gen.generate_email(
        "Test Email", template, **req.query_params
    )

    mailer.sendmail(req.query_params["to"], subject, text, html)

    return HTMLResponse(html)


@app.get("/env", include_in_schema=False)
async def get_env(
    settings: dependencies.SettingsDep,
):
    return settings.environment


@app.post("/sso/google")
async def google_sso_login(
    req2: dict,
    settings: dependencies.SettingsDep,
    google_sso: dependencies.GoogleSSODep,
    users: dependencies.UserRepositoryDep,
    mailer: dependencies.MailerDep,
    email_gen: dependencies.EmailGeneratorDep,
    x_app_platform: str | None = Header(None),
):
    try:
        req = GoogleSSORequest.model_validate(req2)
    except Exception as exc:
        print(req2)
        raise HTTPException(400, detail="Invalid request") from exc

    try:
        print(req.id_token)
        payload = google_sso.validate_id_token(req.id_token)

        email = payload.get("email", req.email)
        name = req.name or payload.get("name")
    except InvalidIDToken as exc:
        print("Failed to validate ID token from google", exc)
        raise HTTPException(
            status_code=401, detail="Failed to authenticate via Google"
        ) from exc

    req_user_id: str = req.user_id or payload["sub"]

    user = await users.get_user_by_sso_id(str(req_user_id))
    if user:
        print("User exists", str(user.id))

        # If google's user_id yields us a user, we can continue on with regular
        # workflow of logging in with no creation of users.

        refresh_token_obj = await users.insert_new_refresh_token(str(user.id))
        refresh_token = refresh_token_obj.refresh_token

        access_token = create_access_token_from_user(settings, user)

        current_user = users.from_db_user(user)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": current_user,
        }

    # Create the user if it does not exist, now.
    if not email:
        print("No email attached to request")
        raise HTTPException(400, detail="email is required for non-existent users")

    user = await users.get_user_by_email(email)

    if not user:
        user = DbUser(
            email=email,
            name=name,
            # Why True? Our user has been verified by virtue of the whole apple thing.
            is_verified=True,
            roles=[UserRole.CONSUMER],
            password_hash="",
        )

        user_id = await users.insert_user(user)
    else:
        user_id = user.id

    sso_user = SsoUser(id=req_user_id, provider="google", user_id=user_id)
    await users.insert_sso_user(sso_user)
    refresh_token_obj = await users.insert_new_refresh_token(str(user.id))

    # Verify the user
    await users.update_user_to_verified(user_id)

    access_token = create_access_token_from_user(settings, user)

    current_user = users.from_db_user(user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_obj.refresh_token,
        "token_type": "bearer",
        "user": current_user,
    }


@app.post("/sso/apple")
async def apple_sso_login(
    req2: dict,
    settings: dependencies.SettingsDep,
    apple_sso: dependencies.AppleSSODep,
    users: dependencies.UserRepositoryDep,
    user_errors: dependencies.UserErrorsDep,
    redis: dependencies.RedisDep,
    mailer: dependencies.MailerDep,
    email_gen: dependencies.EmailGeneratorDep,
):
    def error(detail, status_code, **others):
        user_errors.error(
            "sso", None, "/sso/apple", status_code=status_code, detail=detail, **others
        )

    try:
        req = AppleSSORequest.model_validate(req2)
    except Exception as exc:
        error(
            "Unknown issue occurred while validating Apple SSO request",
            status_code=500,
            req=jsonable_encoder(req2),
        )
        print(req2)
        raise exc

    try:
        payload = apple_sso.validate_id_token(req.identity_token)
        if req.user_id and req.user_id != payload["sub"]:
            print("Apple SSO request user_id does not match ID token")
            error(
                "Apple SSO request user_id does not match ID token",
                401,
                req=jsonable_encoder(req),
            )

            raise HTTPException(
                status_code=401, detail="Failed to authenticate via Apple ID"
            )

    except InvalidIDToken as exc:
        print("Failed to validate ID token from apple", exc)
        error(
            "Failed to validate ID token from apple",
            401,
            exc=str(exc),
            req=jsonable_encoder(req),
        )

        raise HTTPException(
            status_code=401, detail="Failed to authenticate via Apple ID"
        ) from exc

    if not req.user_id and not payload.get("nonce"):
        error("User ID or nonce required.", 400)
        raise HTTPException(status_code=400, detail="User ID or nonce required.")

    if nonce := payload.get("nonce"):
        getme = await redis.get(f"nonce:{nonce}")
        if not getme:
            error("nonce not available", 401)
            raise HTTPException(status_code=401, detail="nonce not available")
        else:
            await redis.delete(f"nonce:{nonce}")

    auth_res = None
    if not req.authorization_code:
        print("Apple SSO request did not provide authorizationCode")
        error(
            "Apple SSO request did not provide authorizationCode",
            401,
            req=jsonable_encoder(req),
        )

        raise HTTPException(
            status_code=401,
            detail="Apple SSO request did not provide authorizationCode",
        )

    client_id = payload.get("aud")
    try:
        auth_res = await apple_sso.get_auth_from_code(
            req.authorization_code, client_id=client_id
        )
    except HTTPStatusError as exc:
        print("Failed to authenticate via Apple ID, get_auth_from_code", exc)
        raise HTTPException(
            status_code=401, detail="Failed to authenticate via Apple ID"
        ) from exc

    # At this point, we've authenticated via apple SSO, we just need to do the
    # things now.

    user = await users.get_user_by_sso_id(payload.get("sub"))
    token = None
    if user:
        print("User exists", str(user.id))

        # If apple's user_id yields us a user, we can continue on with regular
        # workflow of logging in with no creation of users.

        if not req.user_id:
            raise HTTPException(400, detail="Apple SSO request user_id not provided.")

        token = await users.get_user_token_by_sso_id(req.user_id)
        if not token and auth_res.refresh_token:
            print("Refresh token does not exist, creating one")
            await _create_refresh_token(users, auth_res.refresh_token, str(user.id))
        elif token:
            print("Reauthorizing from refresh token")
            auth_res = await apple_sso.get_auth_from_refresh_token(token.refresh_token)
            if auth_res.refresh_token:
                print("Updating refresh token")
                token.refresh_token = auth_res.refresh_token
                await users.update_refresh_token(token)

        access_token = create_access_token_from_user(settings, user)

        current_user = users.from_db_user(user)

        return {
            "access_token": access_token,
            "refresh_token": auth_res.refresh_token,
            "token_type": "bearer",
            "user": current_user,
        }

    # Create the user if it does not exist, now.
    if not req.email:
        print("No email attached to request")
        raise HTTPException(400, detail="email is required for non-existent users")

    user = await users.get_user_by_email(req.email)

    if not user:
        name = (
            req.first_name
            if req.last_name is None
            else f"{req.first_name} {req.last_name}"
        )

        user = DbUser(
            email=req.email,
            name=name or "No Name Provided",
            # Why True? Our user has been verified by virtue of the whole apple thing.
            is_verified=True,
            roles=[UserRole.CONSUMER],
            password_hash="",
        )

        user_id = await users.insert_user(user)
    else:
        user_id = user.id

    sso_user_id = payload.get("sub", req.user_id)
    sso_user = SsoUser(id=sso_user_id, provider="apple", user_id=user_id)
    await users.insert_sso_user(sso_user)
    await _create_refresh_token(users, auth_res.refresh_token, str(user.id))

    # Verify the user
    await users.update_user_to_verified(user_id)

    access_token = create_access_token_from_user(settings, user)

    current_user = users.from_db_user(user)
    return {
        "access_token": access_token,
        "refresh_token": auth_res.refresh_token,
        "token_type": "bearer",
        "user": current_user,
    }


@app.post("/login")
async def login_for_access_token(
    settings: dependencies.SettingsDep,
    users: dependencies.UserRepositoryDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    user_errors: dependencies.UserErrorsDep,
    set_cookie: bool = fastapi.Query(default=False, alias="setCookie"),
):
    if form_data.password is not None and len(form_data.password) >= 3172:
        user_errors.error(
            "login",
            None,
            endpoint="/login",
            status_code=400,
            detail="Password is too long",
            email=form_data.username,
        )

        raise HTTPException(
            status_code=400,
            detail="Password is too long",
        )

    email = form_data.username.lower()
    try:
        user = await users.authenticate_user(email, form_data.password)
    except PasswordSizeError:
        user_errors.error(
            "login",
            None,
            endpoint="/login",
            status_code=400,
            detail="Password is too long",
            email=email,
        )
        raise HTTPException(
            status_code=400,
            detail="Password is too long",
        )
    except UnknownHashError:
        user_errors.error(
            "login",
            None,
            endpoint="/login",
            status_code=401,
            detail="Incorrect email or password",
            email=email,
        )
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user:
        user_errors.error(
            "login",
            None,
            endpoint="/login",
            status_code=401,
            detail="Incorrect email or password",
            email=email,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token_from_user(settings, user)
    refresh_token_obj = await users.insert_new_refresh_token(str(user.id))
    refresh_token = refresh_token_obj.refresh_token
    token_type = "bearer"

    if set_cookie:
        response.set_cookie(
            "accessToken",
            access_token,
            httponly=True,
            expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=True if settings.environment in ["production", "staging"] else False,
            samesite="strict",
            domain=settings.cookie_domain,
        )

    user = users.from_db_user(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": token_type,
        "user": user,
    }


# Logout
@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("accessToken")
    return {"message": "Logged out"}


@app.get("/user-roles")
async def get_user_roles() -> list[str]:
    return [role.value for role in USER_ROLES]


class BeginPasswordResetRequest(CamelModel):
    email: str


@app.get("/password-reset")
async def begin_password_reset(
    email: str,
    mailer: dependencies.MailerDep,
    email_gen: dependencies.EmailGeneratorDep,
    users: dependencies.UserRepositoryDep,
):
    wait_seconds = float(secrets.randbelow(1000) / 1000)
    await asyncio.sleep(wait_seconds)
    user = await users.get_user_by_email(email)

    if user:
        reset_code = await users.generate_password_reset(str(user.id))

        subject, text, html = email_gen.generate_password_reset(reset_code)
        mailer.sendmail(user.email, subject, text, html)


class PasswordResetRequest(CamelModel):
    code: str
    email: str
    password: str


@app.post("/password-reset")
async def end_password_reset(
    req: PasswordResetRequest, users: dependencies.UserRepositoryDep
):
    if not await users.check_password_reset(req.email, req.code):
        raise HTTPException(403, detail="Code and Email did not match.")

    await users.reset_password(req.email, req.password)


app.include_router(app_router_users.public_router)
app.include_router(app_router_users.active_user_router)
admin_router.include_router(users.router)
admin_router.include_router(dashboard.router)

app.include_router(admin_router)
app.include_router(app_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8040, log_level="info")
