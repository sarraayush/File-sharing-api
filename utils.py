import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

# def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
#     to_encode = data.copy()
#     expire = datetime.now() + expires_delta
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, "SECRET_KEY", algorithm="HS256")
#     return encoded_jwt

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)  # Default expiration time
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "SECRET_KEY", algorithm="HS256")
    return encoded_jwt


def object_id_to_str(data):
    if isinstance(data, list):
        return [object_id_to_str(item) for item in data]
    elif isinstance(data, dict):
        return {key: object_id_to_str(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data