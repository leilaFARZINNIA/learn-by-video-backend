import time, firebase_admin
from firebase_admin import auth, credentials
from fastapi import Request, HTTPException


if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.ApplicationDefault())

class Identity(dict):
    @property
    def uid(self): return self.get("uid")
    @property
    def email(self): return self.get("email")
    @property
    def is_recent(self):  
        return (time.time() - self.get("auth_time", 0)) <= 300

def get_identity(req: Request) -> Identity:
    authz = req.headers.get("Authorization", "")
    if not authz.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = authz.split()[1]
    try:
        info = auth.verify_id_token(token) 
        return Identity(info)
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
