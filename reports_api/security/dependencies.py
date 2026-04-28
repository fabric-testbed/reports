import asyncio
from typing import Union

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from reports_api.common.globals import GlobalsSingleton
from reports_api.security.fabric_token import FabricToken

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> Union[FabricToken, dict]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = credentials.credentials
    globals_ = GlobalsSingleton.get()
    config = globals_.config
    runtime_config = config.runtime_config
    oauth_config = config.oauth_config

    # Fast path: static bearer token
    if token in runtime_config.get("bearer_tokens", []):
        return {}

    # Slow path: JWKS validation (sync library, run in thread)
    try:
        verify_exp = oauth_config.get("verify-exp", True)
        fabric_token = await asyncio.to_thread(
            globals_.token_validator.validate_token,
            token=token,
            verify_exp=verify_exp,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    if not fabric_token.roles:
        raise HTTPException(
            status_code=401,
            detail=f"{fabric_token.uuid}/{fabric_token.email} is not authorized!",
        )

    # Role-based authorization
    allowed_roles = runtime_config.get("allowed_roles", [])
    for role in fabric_token.roles:
        if role.get("name") in allowed_roles:
            return fabric_token

    raise HTTPException(status_code=401, detail="User is not authorized!")


async def require_bearer_token_only(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = credentials.credentials
    globals_ = GlobalsSingleton.get()
    runtime_config = globals_.config.runtime_config

    if token in runtime_config.get("bearer_tokens", []):
        return {}

    # For POST endpoints, reject user tokens - only static bearer tokens allowed
    raise HTTPException(status_code=401, detail="Only static bearer tokens are accepted for this endpoint")
