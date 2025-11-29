import json

from jwcrypto import jwt, jwk
from datetime import datetime


class InvalidIDToken(Exception):
    pass


class BaseSSO:
    def __init__(self, keys, aud: str | list[str], iss: str | list[str]):
        self.keys = keys
        self.aud = [aud] if isinstance(aud, str) else aud
        self.iss = [iss] if isinstance(iss, str) else iss

    def validate_id_token(self, jwt_token):
        jwt_token = jwt.JWT.from_jose_token(jwt_token)

        validating_key = None
        token_kid = jwt_token.token.jose_header.get("kid", None)
        for key in self.keys:
            if key["kid"] == token_kid:
                validating_key = jwk.JWK.from_json(json.dumps(key))
                break

        if not validating_key:
            raise InvalidIDToken("Couldn't find matching 'kid'")

        jwt_token.validate(validating_key)
        payload = json.loads(jwt_token.token.payload)

        if payload.get("aud", None) not in self.aud:
            raise InvalidIDToken("aud is incorrect")
        if payload.get("iss", None) not in self.iss:
            raise InvalidIDToken("iss is incorrect")
        if (exp := payload.get("exp", None)) and exp < datetime.now().timestamp():
            raise InvalidIDToken("expired token")

        return payload
