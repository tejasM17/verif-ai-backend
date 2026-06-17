from pydantic import BaseModel


class AuthRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    uid: str
    email: str


class TokenResponse(BaseModel):
    idToken: str
    email: str
    localId: str
