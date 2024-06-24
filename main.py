from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import aiofiles
import os
import jwt
from utils import get_password_hash, verify_password, create_access_token,object_id_to_str
from email_utils import send_verification_email

app = FastAPI()

# Database
client = AsyncIOMotorClient('Mongourl')
db = client.fileshare

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    files: list

class ClientUserInDB(BaseModel):
    email: str
    username: str
    hashed_password: str
    is_verified: bool = False

class SignupData(BaseModel):
    email: str
    username: str
    password: str

# Dummy data initialization
@app.on_event("startup")
async def startup_db_client():
    user = await db.user.find_one({"username": "ops_user"})
    if not user:
        await db.user.insert_one({"username": "ops_user", "hashed_password": "hashedpassword123", "files": []})
    
    # Create the files directory if it doesn't exist
    if not os.path.exists('files'):
        os.makedirs('files')

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = await db.user.find_one({"username": "ops_user"})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.user.find_one({"username": form_data.username})
    if not user or form_data.password != "password123":  # Replace with hashed password check
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    return {"access_token": user["username"], "token_type": "bearer"}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user)):
    if file.content_type not in ["application/vnd.openxmlformats-officedocument.presentationml.presentation", 
                                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")

    file_location = f"files/{file.filename}"
    async with aiofiles.open(file_location, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    file_data = {
        "filename": file.filename,
        "file_link": file_location,
        "uploaded_by": current_user["username"]
    }
    result = await db.filesupload.insert_one(file_data)
    await db.user.update_one({"username": current_user["username"]}, {"$push": {"files": result.inserted_id}})

    return {"info": "file uploaded successfully"}

@app.post("/client/signup")
async def client_signup(data: SignupData):
    email = data.email
    username = data.username
    password = data.password
    print(email , " aaush ", password  , " " ,username  )
    hashed_password = get_password_hash(password)
    token = create_access_token({"email": email, "username": username})
    encrypted_url = f"http://localhost:8000/client/verify?token={token}"

    user_data = {"email": email, "username": username, "hashed_password": hashed_password, "is_verified": False}
    await db.clientuser.insert_one(user_data)
    send_verification_email(email, encrypted_url)
    
    return {"message": "Signup successful! Please verify your email.", "verification_url": encrypted_url}

@app.get("/client/verify")
async def verify_email(token: str):
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        await db.clientuser.update_one({"email": email}, {"$set": {"is_verified": True}})
        return {"message": "Email verification successful!"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@app.post("/client/token", response_model=Token)
async def client_login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.clientuser.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not user["is_verified"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified")
    return {"access_token": user["username"], "token_type": "bearer"}

@app.get("/client/files")
async def list_files():
    files = await db.filesupload.find().to_list(length=None)
    files = object_id_to_str(files)
    return files

@app.get("/client/download/{file_id}")
async def download_file(file_id: str):
    file = await db.filesupload.find_one({"_id": ObjectId(file_id)})
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return {"file_link": file["file_link"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
