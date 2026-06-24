from pydantic import BaseModel, EmailStr


class AuthRequest(BaseModel):
    email: str
    password: str
    role: str | None = None


class GoogleAuthRequest(BaseModel):
    id_token: str


class GithubAuthRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    uid: str
    email: EmailStr
    displayName: str | None = None
    photoUrl: str | None = None
    role: str | None = None


class TokenResponse(BaseModel):
    idToken: str
    email: str
    localId: str
    displayName: str | None = None
    photoUrl: str | None = None
    role: str | None = None
