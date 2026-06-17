import httpx
from firebase_admin import auth
from app.core.config import settings

FIREBASE_SIGN_IN_URL = (
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
    f"?key={settings.FIREBASE_WEB_API_KEY}"
)


class FirebaseRepository:
    def create_user(self, email: str, password: str):
        return auth.create_user(email=email, password=password)

    def verify_token(self, token: str):
        return auth.verify_id_token(token, clock_skew_seconds=10)

    async def sign_in_with_password(self, email: str, password: str):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                FIREBASE_SIGN_IN_URL,
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True,
                },
            )
        return resp.json()
