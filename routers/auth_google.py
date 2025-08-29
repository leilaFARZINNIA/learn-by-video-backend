# routers/auth_google.py
import os, base64, hashlib, secrets, time, urllib.parse, json
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl
from fastapi import APIRouter, Response, Request, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
from jose import jwt
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from dotenv import load_dotenv

from db.postgres import get_db
from crud.users import upsert_user_google
from auth.cookies import set_session_cookie, clear_session_cookie
from auth.deps import current_user
from models.user import UserORM

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
CLIENT_ORIGIN_DEFAULT = os.getenv("CLIENT_ORIGIN", "http://localhost:8081")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8080/auth/google/callback")
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me")


ALLOWED_REDIRECT_SCHEMES = {"http", "https", "learnbyvideo", "exp", "exp+learnbyvideo"}
#                                          

router = APIRouter()

# ---------- helpers ----------
def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def b64url_json(obj: dict) -> str:
    return b64url(json.dumps(obj).encode())

def b64url_to_json(s: str) -> dict:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return json.loads(base64.urlsafe_b64decode(s + pad).decode())

def add_query(url: str, key: str, value: str) -> str:
    p = urlparse(url)
    q = dict(parse_qsl(p.query))
    q[key] = value
    return urlunparse(p._replace(query=urlencode(q)))

def set_temp_cookie(res: Response, key: str, value: str):
 
    res.set_cookie(key=key, value=value, max_age=300, httponly=True, samesite="lax", secure=False, path="/")

def clear_cookie(res: Response, key: str):
    res.delete_cookie(key=key, path="/")

def is_allowed_redirect(uri: str) -> bool:
    try:
        p = urlparse(uri)
        return bool(p.scheme) and p.scheme in ALLOWED_REDIRECT_SCHEMES
    except Exception:
        return False

# ---------- routes ----------

@router.get("/auth/google/start")
async def google_start(redirect_uri: str | None = Query(None)):
  
    xsrf = b64url(secrets.token_bytes(16))
    verifier = b64url(secrets.token_bytes(32))
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())

    client_redirect = redirect_uri if (redirect_uri and is_allowed_redirect(redirect_uri)) else None
    composed_state = b64url_json({"xsrf": xsrf, "redir": client_redirect})

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,      
        "response_type": "code",
        "scope": "openid email profile",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": composed_state,
        "prompt": "select_account",
    }
    q = urllib.parse.urlencode(params)
    res = RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{q}", status_code=302)


    set_temp_cookie(res, "g_state", xsrf)
    set_temp_cookie(res, "g_verifier", verifier)
    if client_redirect:
        set_temp_cookie(res, "g_redir", client_redirect)
    return res


@router.get("/auth/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    cookies = request.cookies


    try:
        st = b64url_to_json(state or "")
        xsrf = st.get("xsrf")
        redir_from_state = st.get("redir")
    except Exception:
        raise HTTPException(400, "Bad state")

    
    if not xsrf or xsrf != cookies.get("g_state"):
        raise HTTPException(400, "Invalid state")

    verifier = cookies.get("g_verifier")
    if not verifier or not code:
        raise HTTPException(400, "Missing code/verifier")

 
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20.0,
        )
    if token_res.status_code != 200:
        raise HTTPException(401, "Token exchange failed")
    tokens = token_res.json()
    id_tok = tokens.get("id_token")
    if not id_tok:
        raise HTTPException(401, "Token exchange failed")

    try:
        payload = google_id_token.verify_oauth2_token(id_tok, google_requests.Request(), GOOGLE_CLIENT_ID)
    except Exception:
        raise HTTPException(401, "Invalid Google token")

    user = await upsert_user_google(
        db,
        google_sub=payload["sub"],
        email=payload.get("email"),
        name=payload.get("name"),
        avatar=payload.get("picture"),
    )


    session_payload = {"uid": str(user.user_id), "iat": int(time.time())}
    session_jwt = jwt.encode(session_payload, SESSION_SECRET, algorithm="HS256")

    res_target = cookies.get("g_redir") or redir_from_state or f"{CLIENT_ORIGIN_DEFAULT}/oauthredirect"
    if not is_allowed_redirect(res_target):
        res_target = f"{CLIENT_ORIGIN_DEFAULT}/oauthredirect"

    
    scheme = urlparse(res_target).scheme
    if scheme in ("learnbyvideo", "exp", "exp+learnbyvideo"):
        res_target = add_query(res_target, "token", session_jwt)

    print("[oauth] redirecting to:", res_target)

    res = RedirectResponse(url=res_target, status_code=302)
    set_session_cookie(res, session_jwt)


    clear_cookie(res, "g_state")
    clear_cookie(res, "g_verifier")
    clear_cookie(res, "g_redir")
    return res


class GoogleMobileIn(BaseModel):
    id_token: str

@router.post("/auth/google/mobile")
async def google_mobile(body: GoogleMobileIn, db: AsyncSession = Depends(get_db)):
    try:
        payload = google_id_token.verify_oauth2_token(body.id_token, google_requests.Request(), GOOGLE_CLIENT_ID)
    except Exception:
        raise HTTPException(401, "Invalid Google token")

    user = await upsert_user_google(
        db,
        google_sub=payload["sub"],
        email=payload.get("email"),
        name=payload.get("name"),
        avatar=payload.get("picture"),
    )

    session_payload = {"uid": str(user.user_id), "iat": int(time.time())}
    session_jwt = jwt.encode(session_payload, SESSION_SECRET, algorithm="HS256")

    return {
        "token": session_jwt,
        "user": {
            "uid": str(user.user_id),
            "email": user.email,
            "name": user.name,
            "avatar": user.avatar,
        },
    }

@router.get("/api/me")
async def me(u: UserORM = Depends(current_user)):
    return {
        "user": {
            "uid": str(u.user_id),
            "email": u.email,
            "name": u.name,
            "avatar": u.avatar,
            "has_password": bool(u.password_hash),
            "provider": "google" if u.google_sub else "local",
        }
    }

@router.post("/auth/logout")
async def logout():
    res = JSONResponse({"ok": True})
    clear_session_cookie(res)
    return res

@router.get("/done")
async def done():
    return {"ok": True, "hint": "Session cookie set. Now call GET /api/me"}
