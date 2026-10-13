from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
from database import get_user_hash, user_exists, get_password_hash, get_user_data, get_user_role, log_rag_request
from fastapi.middleware.cors import CORSMiddleware
from ragConnecter import rag_retrieve
from guardrails import check_input, check_output
import markdown


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    emp_id: int
    password: str

class QueryPayload(BaseModel):
    user_input: str

class Token(BaseModel):
    access_token: str
    token_type: str

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
security = HTTPBearer()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_access_token(data: dict,expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(empid: int, password: str):
    stored_hash = get_user_hash(empid)[0][0]
    return password_hash.verify(password, stored_hash)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = token.strip()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        empid: str | None = payload.get("sub")
        if empid is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
        
    return int(empid)

@app.post("/user/query")
async def user_query(payload: QueryPayload, current_emp_id: int = Depends(get_current_user)):
    user_role = get_user_role(current_emp_id)
    role_str = user_role[0] if user_role else "unknown"

    input_check = check_input(payload.user_input)
    if input_check["blocked"]:
        log_rag_request(
            emp_id=current_emp_id,
            role=role_str,
            query=payload.user_input,
            response=input_check["reason"],
            guardrail_blocked=True,
        )
        return {
            "message": f"Query blocked by input guardrail for employee #{current_emp_id}",
            "input_received": payload.user_input,
            "rag_response": input_check["reason"],
            "user_role": user_role,
            "guardrail_blocked": True,
        }

    raw_response = await rag_retrieve(payload.user_input, user_role)

    output_check = check_output(raw_response)
    if output_check["blocked"]:
        log_rag_request(
            emp_id=current_emp_id,
            role=role_str,
            query=payload.user_input,
            response=output_check["reason"],
            guardrail_blocked=True,
        )
        return {
            "message": f"Response blocked by output guardrail for employee #{current_emp_id}",
            "input_received": payload.user_input,
            "rag_response": output_check["reason"],
            "user_role": user_role,
            "guardrail_blocked": True,
        }

    rag_response = markdown.markdown(raw_response)
    log_rag_request(
        emp_id=current_emp_id,
        role=role_str,
        query=payload.user_input,
        response=raw_response,
        guardrail_blocked=False,
    )

    return {
        "message": f"Processed query for employee #{current_emp_id}",
        "input_received": payload.user_input,
        "rag_response": rag_response,
        "user_role": user_role,
        "guardrail_blocked": False,
    }

@app.post("/login")
async def login_user(user_login: User):
    if not user_exists(user_login.emp_id) or not authenticate_user(user_login.emp_id,user_login.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub": str(user_login.emp_id)},
        expires_delta = access_token_expires
    )
    user = get_user_data(user_login.emp_id)
    return {"access_token": access_token, "token_type": "bearer"}