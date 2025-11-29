from datetime import datetime, timedelta
import httpx
from jwcrypto import jwt, jwk
from pydantic import BaseModel, Field
from enum import Enum

from python_api.models import CamelModel
from python_api.settings import Settings
from python_api.repositories.users import UserRepository
from python_api.user_errors import UserErrors
from python_api.sso import BaseSSO


class AppleGrantType(Enum):
    REFRESH_TOKEN = "refresh_token"
    AUTHORIZATION_CODE = "authorization_code"


def default_auth_token_exp() -> int:
    return int((datetime.now() + timedelta(seconds=300)).timestamp())


def default_auth_token_iat() -> int:
    return int(datetime.now().timestamp())


class AppleAuthToken(BaseModel):
    iss: str = Field(alias="team_id")
    iat: int = Field(default_factory=default_auth_token_iat)
    exp: int = Field(default_factory=default_auth_token_exp)
    aud: str = "https://appleid.apple.com"
    sub: str = Field(alias="client_id")


class AppleSSORequest(CamelModel):
    identity_token: str
    authorization_code: str
    user_id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class AppleAuthRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str | None = None
    grant_type: AppleGrantType
    refresh_token: str | None = None


class AppleRevokeTokenRequest(BaseModel):
    client_id: str
    client_secret: str
    token: str
    token_type_hint: str = "refresh_token"


class AppleAuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None
    id_token: str


class AppleSSO(BaseSSO):
    def __init__(
        self,
        settings: Settings,
        users: UserRepository,
        errors: UserErrors,
        keys: list[dict[str, str]],
    ):
        super().__init__(
            keys,
            [settings.apple_services_id],
            "https://appleid.apple.com",
        )
        self.users = users
        self.settings = settings
        self.errors = errors

    def _make_client_secret(self, client_id: str):
        payload = AppleAuthToken(
            team_id=self.settings.apple_team_id, client_id=client_id
        )

        with open(self.settings.apple_sso_key_path, "rb") as key_file:
            key = jwk.JWK.from_pem(key_file.read())

        secret = jwt.JWT(
            header={"alg": "ES256", "kid": self.settings.apple_sso_key_id},
            claims=payload.model_dump(mode="json"),
        )
        secret.make_signed_token(key)
        return secret.serialize()

    async def _execute_auth_request(self, auth_request: AppleAuthRequest):
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://appleid.apple.com/auth/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=auth_request.model_dump(mode="json"),
            )

            if res.is_error:
                self.errors.error(
                    "apple-sso",
                    None,
                    endpoint=None,
                    requestBody=auth_request.model_dump(mode="json"),
                    responseCode=res.status_code,
                    responseBody=res.text,
                )

                print("Information on Apple SSO error:")
                print(f"Request body: {auth_request.model_dump(mode='json')}")
                print(f"Status code: {res.status_code}")
                print("Response body:")
                print(res.text)

            res.raise_for_status()

            auth_res = AppleAuthResponse(**res.json())
            return auth_res

    async def revoke_user_by_refresh_token(self, refresh_token: str):
        req = AppleRevokeTokenRequest(
            client_id=self.settings.apple_services_id,
            client_secret=self._make_client_secret(
                client_id=self.settings.apple_services_id
            ),
            token=refresh_token,
            token_type_hint="refresh_token",
        )

        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://appleid.apple.com/auth/revoke",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=req.model_dump(mode="json"),
            )

            res.raise_for_status()

    async def get_auth_from_code(self, authorization_code: str, client_id=None):
        client_secret = self._make_client_secret(
            client_id=client_id or self.settings.apple_services_id
        )
        auth_request = AppleAuthRequest(
            client_id=client_id or self.settings.apple_services_id,
            client_secret=client_secret,
            code=authorization_code,
            grant_type=AppleGrantType.AUTHORIZATION_CODE,
            refresh_token=None,
        )

        return await self._execute_auth_request(auth_request)

    async def get_auth_from_refresh_token(self, refresh_token: str, client_id=None):
        client_secret = self._make_client_secret(
            client_id=client_id or self.settings.apple_services_id
        )
        auth_request = AppleAuthRequest(
            client_id=client_id or self.settings.apple_services_id,
            client_secret=client_secret,
            code=None,
            grant_type=AppleGrantType.REFRESH_TOKEN,
            refresh_token=refresh_token,
        )

        return await self._execute_auth_request(auth_request)
