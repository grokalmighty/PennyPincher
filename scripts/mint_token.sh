#!/usr/bin/env bash
set -euo pipefail
# Prints a JWT signed with $JWT_SECRET or 'devsecret'
SECRET="${JWT_SECRET:-devsecret}"

try_pyjwt() {
  python - <<PY 2>/dev/null || return 1
import jwt, datetime
print(jwt.encode({"sub":"1","exp": datetime.datetime.utcnow()+datetime.timedelta(hours=2)},
                 "$SECRET", algorithm="HS256"))
PY
}

try_venv() {
  if [ -x backend/venv/bin/python ]; then
    backend/venv/bin/python - <<PY 2>/dev/null || return 1
import jwt, datetime
print(jwt.encode({"sub":"1","exp": datetime.datetime.utcnow()+datetime.timedelta(hours=2)},
                 "$SECRET", algorithm="HS256"))
PY
  else
    return 1
  fi
}

try_pure() {
  python - <<'PY' 2>/dev/null || return 1
import base64, json, hmac, hashlib, time, os
secret = os.environ.get("JWT_SECRET","devsecret").encode()
b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b'=').decode()
head=b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
pay=b64(json.dumps({"sub":"1","exp":int(time.time())+7200}).encode())
sig=b64(hmac.new(secret, f"{head}.{pay}".encode(), hashlib.sha256).digest())
print(f"{head}.{pay}.{sig}")
PY
}

try_pyjwt || try_venv || try_pure
