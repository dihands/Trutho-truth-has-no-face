from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth
from utils.anonymous_names import generate_anonymous_username

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.TokenResponse)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    username = (data.username or "").strip()
    if not username:
        username = generate_anonymous_username()

    # Ensure username uniqueness
    base = username
    counter = 1
    while db.query(models.User).filter(models.User.username == username).first():
        username = f"{base}_{counter}"
        counter += 1

    user = models.User(
        username=username,
        password_hash=auth.hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(access_token=token, username=user.username, user_id=user.id)


@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if not user or not auth.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")

    token = auth.create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(access_token=token, username=user.username, user_id=user.id)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(auth.require_user)):
    return current_user


@router.get("/suggest-username")
def suggest_username():
    return {"suggestions": [generate_anonymous_username() for _ in range(6)]}
