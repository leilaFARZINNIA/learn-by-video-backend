# routers/auth_public.py
from fastapi import APIRouter, Query, Response, HTTPException
from pydantic import BaseModel, EmailStr
from firebase_admin import auth as fb_auth

router = APIRouter(prefix="/auth", tags=["auth-public"])


class CheckOut(BaseModel):

    exists: bool
    has_password: bool | None = None
    provider: str | None = None 


@router.get("/health")
async def health():

    return {"ok": True}


@router.get("/check", response_model=CheckOut)
async def check(response: Response, email: EmailStr = Query(..., description="Email address to check"
)):
 
    response.headers["Cache-Control"] = "no-store"

    email_norm = str(email).lower()

    try:
        u = fb_auth.get_user_by_email(email_norm)
    except fb_auth.UserNotFoundError:
        return {"exists": False}
    except Exception as e:
        
        raise HTTPException(status_code=502, detail=f"FIREBASE_LOOKUP_FAILED: {e}")

    provider_ids = {p.provider_id for p in (u.provider_data or [])}
    has_pw = "password" in provider_ids

    # provider
    if "google.com" in provider_ids and has_pw:
        summary = "google+password"
    elif "google.com" in provider_ids:
        summary = "google"
    elif has_pw:
        summary = "local"
    else:
      
        summary = next(iter(provider_ids), None)

    return {"exists": True, "has_password": has_pw, "provider": summary}
