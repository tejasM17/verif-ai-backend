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

    def google_login(self, id_token: str):
        try:
            decoded = repo.verify_token(id_token)
            uid = decoded["uid"]
            email = decoded.get("email", "")
            display_name = decoded.get("name", "")
            photo_url = decoded.get("picture", "")
            return {
                "idToken": id_token,
                "email": email,
                "localId": uid,
                "displayName": display_name,
                "photoUrl": photo_url,
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    def github_login(self, id_token: str):
        try:
            decoded = repo.verify_token(id_token)
            uid = decoded["uid"]
            email = decoded.get("email", "")
            display_name = decoded.get("name", "")
            photo_url = decoded.get("picture", "")
            return {
                "idToken": id_token,
                "email": email,
                "localId": uid,
                "displayName": display_name,
                "photoUrl": photo_url,
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    def get_current_user(self, token: str):
        try:
            decoded = repo.verify_token(token)
            return {
                "uid": decoded["uid"],
                "email": decoded.get("email", ""),
                "displayName": decoded.get("name", ""),
                "photoUrl": decoded.get("picture", ""),
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
