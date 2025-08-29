# auth/cookies.py
import os
from urllib.parse import urlparse
from fastapi import Response
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "development").lower()           
CLIENT_ORIGIN = os.getenv("CLIENT_ORIGIN", "http://localhost:8081")
COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "sid")     
DEFAULT_MAX_AGE_DAYS = int(os.getenv("SESSION_MAX_AGE_DAYS", "7"))

def _cookie_opts():
   
    is_prod = ENV in ("prod", "production")
    same_site = "none" if is_prod else "lax"
    secure = True if same_site == "none" else False

    
    domain = None
    try:
        host = urlparse(CLIENT_ORIGIN).hostname
        if is_prod and host and host not in ("localhost", "127.0.0.1"):
            
            domain = host
    except Exception:
        pass

    return {
        "httponly": True,
        "samesite": same_site,  
        "secure": secure,
        "path": "/",
        "domain": domain,
    }

def set_session_cookie(res: Response, token: str, days: int = DEFAULT_MAX_AGE_DAYS):
    opts = _cookie_opts()
    res.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=days * 24 * 3600,
        httponly=opts["httponly"],
        samesite=opts["samesite"],
        secure=opts["secure"],
        path=opts["path"],
        domain=opts["domain"],
    )

def clear_session_cookie(res: Response):
    opts = _cookie_opts()
    res.delete_cookie(
        key=COOKIE_NAME,
        path=opts["path"],
        domain=opts["domain"],
    )
