from fastapi import HTTPException
from app.repositories.firebase_repository import FirebaseRepository

repo = FirebaseRepository()


class AuthService:
    def signup(self, email: str, password: str):
        try:
            user = repo.create_user(email, password)
            return {"uid": user.uid, "email": user.email}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def login(self, email: str, password: str):
        data = await repo.sign_in_with_password(email, password)
        if "idToken" not in data:
            raise HTTPException(
                status_code=401,
                detail=data.get("error", {}).get("message", "Login failed"),
            )
        return {
            "idToken": data["idToken"],
            "email": data["email"],
            "localId": data["localId"],
        }

    def get_current_user(self, token: str):
        try:
            decoded = repo.verify_token(token)
            return {"uid": decoded["uid"], "email": decoded.get("email", "")}
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
