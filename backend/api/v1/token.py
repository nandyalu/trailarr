from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError

from config.settings import app_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    """Creates a JWT access token. \n
    Args:
        data (dict): The data to encode in the token.
        expires_delta (timedelta, optional): The token's expiration time. \
            Defaults to 15 minutes. \n
    Returns:
        str: The encoded JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, app_settings.api_key, algorithm="HS256"
    )
    return encoded_jwt


def verify_token(
    token: str, credentials_exception: HTTPException
) -> TokenData:
    """Verifies a JWT access token. \n
    Args:
        token (str): The token to verify.
        credentials_exception (HTTPException): The exception to raise if the \
            token is invalid. \n
    Returns:
        TokenData: The decoded token data."""
    try:
        payload = jwt.decode(token, app_settings.api_key, algorithms=["HS256"])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    return token_data


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TokenData:
    """Gets the current user from the JWT access token. \n
    Args:
        token (str): The token to verify. \n
    Returns:
        TokenData: The decoded token data."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)
