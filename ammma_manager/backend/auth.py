import hashlib
import os
import secrets
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# Configurações de segurança (Uso de Variáveis de Ambiente)
from dotenv import load_dotenv
load_dotenv() # Carrega as variáveis do arquivo .env, se existir

SECRET_KEY = os.getenv("SECRET_KEY", "ammma-3d-secret-key-super-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 

def get_password_hash(password: str) -> str:
    # Usando PBKDF2 (nativo do Python, ultra seguro e compatível)
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${hash_obj.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, stored_hash = hashed_password.split('$')
        hash_obj = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
        return secrets.compare_digest(hash_obj.hex(), stored_hash)
    except:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
