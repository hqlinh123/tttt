import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("firebase-service-account.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

def verify_firebase_token(id_token: str) -> dict:
    return auth.verify_id_token(
        id_token,
        check_revoked=True,   # optional nhưng nên có
    )