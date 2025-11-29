import json
from typing import Any
from datetime import datetime, timedelta, timezone
from jwcrypto import common, jwk, jwt

from python_api.models.users import DbUser

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120


def compatibility_compare(app_platform, app_build, apple_build, google_build=None):
    """
    Return true if compatibility needs to be applied.
    """
    if app_platform == "Apple" and int(app_build) <= int(apple_build):
        return True

    if app_platform == "Android":
        if google_build is None:
            return False
        elif int(app_build) <= int(google_build):
            return True

    return False


def create_access_token_from_user(
    settings, user: DbUser, fresh=False, expires_delta: timedelta | None = None
):
    expires_delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    return create_access_token(
        settings,
        data={
            "sub": str(user.id),
            "roles": [r.value for r in user.roles],
            "fresh": fresh,
            "restricted": user.restricted,
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def load_key(settings):
    key = jwk.JWK.from_pem(open(settings.jwt_signing_key, "rb").read())
    key.update({"use": "sig", "alg": ALGORITHM})
    return key


def get_jwks(settings):
    key = load_key(settings)
    return {"keys": [key.export_public(as_dict=True)]}


signing_key = None


def validate_token(token: str, settings):
    global signing_key
    if signing_key is None:
        signing_key = load_key(settings)

    valid_kids = [signing_key.key_id]

    jwt_token = jwt.JWT.from_jose_token(token)
    if jwt_token.token.jose_header.get("kid") in valid_kids:
        jwt_token.validate(signing_key)
    else:
        raise common.JWException("Invalid kid in token")

    payload = json.loads(jwt_token.token.payload)
    return payload


def create_access_token(
    settings,
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    expire: datetime | None = None,
):
    to_encode = data.copy()
    if not expire:
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
    to_encode.update({"exp": int(expire.timestamp())})
    key = load_key(settings)
    print(key.key_id)

    token = jwt.JWT(header={"alg": ALGORITHM, "kid": key.key_id}, claims=to_encode)
    token.make_signed_token(key)

    return token.serialize()


def try_int(x: Any) -> Any:
    try:
        return int(x)
    except ValueError:
        return x
