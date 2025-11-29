from datetime import datetime, timezone, timedelta
from typing import Annotated


import fastapi
from fastapi import APIRouter, Body, status, Depends, Response, Query, Request
from fastapi.exceptions import HTTPException
from fastapi.encoders import jsonable_encoder
from httpx import HTTPStatusError
from psycopg.errors import UniqueViolation
from typesense.exceptions import ObjectNotFound
from python_api.Error import FileNotFoundException
from python_api.dependencies import (
    AppleSSODep,
    BucketStorageDep,
    CurrentActiveUserDep,
    TrackingDep,
    UserErrorsDep,
    UserRepositoryDep,
    MailerDep,
    SettingsDep,
    refresh_token,
    apple_sso,
    get_current_active_user,
    EmailGeneratorDep,
    AutomatedEmailsDep,
    TransactionsRepositoryDep,
)
from python_api.models import CamelModel
from python_api.sso.apple import AppleSSO
from python_api.models.users import (
    AppUserUpdate,
    UnverifiedUser,
    User,
    AppUser,
    DbUser,
    VerifyEmailCode,
    UpdatePassword,
    UUIDString,
)
from python_api.models.emails import EmailType
from python_api.models.users import UserRole
from python_api.utils import (
    create_access_token_from_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/users", tags=["users"])
active_user_router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(get_current_active_user)]
)
public_router = APIRouter(prefix="/users", tags=["users"])


@public_router.get("/me", response_model=User)
async def read_users_me(current_user: CurrentActiveUserDep):
    return current_user


@public_router.put("/me", response_model=User)
async def update_user(
    current_user: CurrentActiveUserDep,
    users: UserRepositoryDep,
    user_update: AppUserUpdate,
):
    user = await users.update_user_from_app(str(current_user.id), user_update)
    user = users.from_db_user(user)
    if not user or not user.id:
        raise HTTPException(404, "User not found")

    return user


@public_router.get("/me/token")
async def get_user_token(
    settings: SettingsDep,
    users: UserRepositoryDep,
    response: Response,
    user_errors: UserErrorsDep,
    apple: AppleSSO = Depends(apple_sso),
    refresh_token=Depends(refresh_token),
    set_cookie: bool = Query(default=False, alias="setCookie"),
):
    if not refresh_token:
        raise HTTPException(
            403,
            "Attach refresh token via bearer auth",
            headers={"WWW-Authenticate": "Bearer"},
        )

    returned_token = refresh_token.credentials

    token_provider, last_used = await users.get_token_provider_and_last_used(
        refresh_token.credentials
    )

    if token_provider == "apple":
        try:
            auth_res = await apple.get_auth_from_refresh_token(
                refresh_token.credentials
            )
        except HTTPStatusError as e:
            if e.response.status_code == 400:
                raise HTTPException(401, "Refresh Token invalid")
            else:
                raise e

        access_token = auth_res.access_token
        # We got here, so that means the refresh token is valid and
        # so is this access token. Regenerate the access token
        # with one we recognize.

        current_user = await users.get_user_by_refresh_token(refresh_token.credentials)
        if current_user and current_user.restricted:
            raise HTTPException(418, "Restricted user")

        if not current_user:
            print("No user found for refresh token", refresh_token.credentials)
            raise HTTPException(401, "Refresh Token invalid")

        access_token = create_access_token_from_user(settings, current_user)

        if auth_res.refresh_token:
            returned_token = auth_res.refresh_token
            await users.update_refresh_token_by_token(
                refresh_token.credentials, returned_token
            )

        await users.refresh_token_used(refresh_token.credentials)
    else:
        current_user = await users.get_user_by_refresh_token(refresh_token.credentials)
        if current_user and current_user.restricted:
            raise HTTPException(418, "Restricted user")
        create_new = False
        if (
            last_used
            and last_used
            > datetime.now().timestamp() - (ACCESS_TOKEN_EXPIRE_MINUTES / 2) * 60
        ):
            create_new = True

        if current_user:
            access_token = create_access_token_from_user(
                settings, current_user, fresh=False
            )

            if not create_new:
                await users.refresh_token_used(refresh_token.credentials)
            else:
                token_obj = await users.insert_new_refresh_token(current_user.id)
                returned_token = token_obj.refresh_token
        else:
            raise HTTPException(401, "Refresh Token invalid")

    user = users.from_db_user(current_user)

    ret = {
        "access_token": access_token,
        "refresh_token": returned_token,
        "token_type": "bearer",
        "user": jsonable_encoder(user),
    }

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
    return ret


@public_router.post(
    "",
    description="Create User",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
)
async def create_user(
    user: AppUser,
    users: UserRepositoryDep,
    mailer: MailerDep,
    email_gen: EmailGeneratorDep,
    x_app_platform: str | None = fastapi.Header(None),
):
    # Check if user email already exist
    email_user = await users.get_user_by_email(user.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exist with that email",
        )

    # Hash password
    db_user = DbUser(
        name=user.name,
        email=user.email,
        is_verified=False,
        password_hash=users.get_password_hash(user.password),
    )

    # Add user to db
    if db_user.roles == []:
        if user.role_requested == UserRole.CONSUMER.value:
            db_user.roles = [UserRole.CONSUMER]
        elif user.role_requested == UserRole.PUBLISHER.value:
            db_user.roles = [UserRole.PUBLISHER]

    try:
        db_user_id = await users.insert_user(db_user)
    except UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exist with that email",
        )

    # Verify email
    email_verification_code = await users.generate_email_verification_code(db_user_id)

    subject, text, html = email_gen.generate_email(
        "Exchequer Verification",
        "verification",
        **{
            "code": email_verification_code,
        },
    )

    mailer.sendmail(to=user.email, subject=subject, mail=text, html=html)

    return await users.get_user_by_id(db_user_id)


@active_user_router.put("/{id}/password", description="Update password")
async def update_password(
    id: str,
    update_password: UpdatePassword,
    users: UserRepositoryDep,
    active_user: CurrentActiveUserDep,
):
    if str(active_user.id).lower() != id.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this user's password",
        )

    user = await users.get_user_by_id(id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist with that id",
        )

    if not await users.verify_password(
        update_password.old_password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Old password does not match"
        )

    new_password_hash = users.get_password_hash(update_password.new_password)

    await users.update_password(id, new_password_hash)

    return {"message": "Password updated"}


class PostUserVerification(CamelModel):
    user: User | UnverifiedUser
    refresh_token: str | None
    access_token: str | None


@public_router.post("/{_id}/verify", response_model=PostUserVerification)
async def verify_email_verification_code(
    _id: str,
    code: VerifyEmailCode,
    users: UserRepositoryDep,
    user_errors: UserErrorsDep,
    mailer: MailerDep,
    email_gen: EmailGeneratorDep,
    settings: SettingsDep,
    response: Response,
    set_cookie: bool = fastapi.Query(default=False, alias="setCookie"),
):
    def error_logger(status_code, detail, user=None, **others):
        info = (
            {"dbCode": user.code, "dbCodeExpiresAt": user.code_expires_at}
            if user
            else {}
        )

        user_errors.error(
            type="verification",
            user_id=_id,
            endpoint="POST /users/{_id}/verify",
            status_code=status_code,
            details={"detail": detail, "receivedCode": code.code, **info, **others},
        )

    user = await users.get_unverified_user_by_id(_id)

    # Check if user exist
    if not user:
        error_logger(404, "User does not exist with that id")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist with that id",
        )

    if user.is_verified:
        return PostUserVerification(
            user=users.from_db_user(user), refresh_token=None, access_token=None
        )

    if not user.code_expires_at:
        error_logger(400, "Code has not been sent", user=user)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Code has not been sent"
        )

    if datetime.now(timezone.utc).replace(tzinfo=timezone.utc) > user.code_expires_at:
        error_logger(400, "Code has expired", user=user)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Code has expired"
        )

    if user.code != code.code:
        error_logger(403, "Code does not match", user=user)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Code does not match"
        )

    await users.update_user_to_verified(_id)
    user = await users.get_user(_id)

    if user and user.is_verified is True:
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
                secure=True
                if settings.environment in ["production", "staging"]
                else False,
                samesite="strict",
                domain=settings.cookie_domain,
            )

        return PostUserVerification(
            user=users.from_db_user(user),
            refresh_token=refresh_token,
            access_token=access_token,
        )
    else:
        return PostUserVerification(
            user=users.from_db_user(user),
            refresh_token=None,
            access_token=None,
        )


@public_router.post("/{_id}/code")
async def resend_email_verification_code(
    _id: str,
    users: UserRepositoryDep,
    mailer: MailerDep,
    email_gen: EmailGeneratorDep,
    user_errors: UserErrorsDep,
):
    email_verification_code = await users.generate_email_verification_code(_id)
    user = await users.get_unverified_user_by_id(_id)
    if not user:
        user_errors.error(
            type="verification",
            endpoint="POST /users/{_id}/code",
            user_id=_id,
            status_code=404,
            details={"detail": "User not found"},
        )
        raise HTTPException(404, detail="User not found")

    subject, text, html = email_gen.generate_email(
        "Exchequer Verification",
        "verification",
        **{
            "code": email_verification_code,
        },
    )

    mailer.sendmail(to=user.email, subject=subject, mail=text, html=html)


@active_user_router.delete("/{_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    _id: str,
    active_user: CurrentActiveUserDep,
    users: UserRepositoryDep,
    apple_sso: AppleSSODep,
    user_errors: UserErrorsDep,
):
    def error_logger(status_code, detail, **others):
        user_errors.error(
            "verification",
            _id,
            endpoint="DELETE /users/{_id}",
            status_code=status_code,
            details={"detail": detail, **others},
        )

    user = await users.get_user_by_id(_id)
    if not user:
        error_logger(404, "User does not exist with that id")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist with that id",
        )

    if (
        str(active_user.id).lower() != _id.lower()
        and UserRole.ADMIN not in active_user.roles
    ):
        email = user.email if user else None
        error_logger(
            403,
            "You do not have permission to delete this user",
            attemptedDeleteEmail=email,
            attemptedDeleteId=_id,
            activeUserEmail=active_user.email,
            activeUserId=active_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this user",
        )

    sso_users = await users.get_sso_users(_id)
    for sso_user in sso_users:
        if sso_user.provider == "apple":
            refresh_token = await users.get_last_refresh_token(
                str(sso_user.user_id), "apple"
            )
            if refresh_token:
                await apple_sso.revoke_user_by_refresh_token(
                    refresh_token.refresh_token
                )
            break

    # Delete user from RevenueCat
    await users.delete_user(_id)


@public_router.post(
    "/{email_id}/unsubscribe", description="Unsubscribe user from emails"
)
async def unsubscribe_user(
    email_id: str,
    users: UserRepositoryDep,
    email_type: EmailType = Query(None, alias="type"),
):
    user = await users.get_user_by_email_id(email_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await users.unsubscribe_user(str(user.id), email_type)
