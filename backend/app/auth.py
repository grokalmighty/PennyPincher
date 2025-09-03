import jwt, os, datetime
from fastapi import Depends, Header, HTTPException 

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
ALGO = "HS256"

"""Create JWT for given user_id"""
def make_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id), # Token must be a string 
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=ALGO)

"""Extract user_id from token or raise 401"""
def get_user_id(authorization: str = Header(None)) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGO])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail=f"Invalid token")