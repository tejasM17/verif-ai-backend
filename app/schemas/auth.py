from pydantic import BaseModel


class AuthRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class GithubAuthRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    uid: str
    email: str
    displayName: str | None = None
    photoUrl: str | None = None


class TokenResponse(BaseModel):
    idToken: str
    email: str
    localId: str
    displayName: str | None = None
    photoUrl: str | None = None
