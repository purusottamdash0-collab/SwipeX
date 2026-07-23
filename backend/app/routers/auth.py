from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
import uuid
from app.database import get_db
from app import models, schemas, auth
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

def token_response(user: models.User) -> dict:
    return {
        "access_token": auth.create_access_token(data={"sub": str(user.id), "role": user.role}),
        "refresh_token": auth.create_refresh_token(user.id),
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role, "avatar_url": user.avatar_url},
    }

@router.post("/register", response_model=schemas.Token)
def register(user_in: schemas.UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = auth.get_password_hash(user_in.password)
    assigned_role = user_in.role
    if assigned_role == "recruiter":
        assigned_role = models.UserRole.RECRUITER_UNVERIFIED.value

    user = models.User(
        email=user_in.email,
        hashed_password=hashed_pw,
        full_name=user_in.full_name,
        role=assigned_role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize empty profile
    profile = models.UserProfile(user_id=user.id)
    db.add(profile)
    db.commit()

    return token_response(user)

@router.post("/login", response_model=schemas.Token)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not auth.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive")
    if auth.password_needs_upgrade(user.hashed_password):
        user.hashed_password = auth.get_password_hash(login_data.password)
        db.commit()

    return token_response(user)

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(payload: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    user_id = auth.decode_refresh_token(payload.refresh_token)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is unavailable")
    return token_response(user)

@router.post("/google", response_model=schemas.Token)
def google_oauth(payload_in: schemas.GoogleLoginRequest, db: Session = Depends(get_db)):
    if not payload_in.google_token:
        raise HTTPException(status_code=400, detail="Google token is required")

    # 1. Verify token via Google API
    token = payload_in.google_token
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
    try:
        response = httpx.get(url, timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Google token signature or expired")
        google_payload = response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google token verification failed: {str(e)}")

    # 2. Check audience client ID
    if settings.GOOGLE_CLIENT_ID:
        if google_payload.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Token audience mismatch")

    email = google_payload.get("email")
    google_id = google_payload.get("sub")
    full_name = google_payload.get("name", "Google User")
    avatar_url = google_payload.get("picture")

    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google account")

    # 3. Check if user already exists
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        # Existing email: link Google account and ensure authentication provider = Google
        user.auth_provider = "google"
        user.google_id = google_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
    else:
        # User does not exist: auto-register with empty profile
        hashed_pw = auth.get_password_hash(str(uuid.uuid4()))
        assigned_role = payload_in.role
        if assigned_role == "recruiter":
            assigned_role = models.UserRole.RECRUITER_UNVERIFIED.value

        user = models.User(
            email=email,
            hashed_password=hashed_pw,
            full_name=full_name,
            avatar_url=avatar_url,
            auth_provider="google",
            google_id=google_id,
            role=assigned_role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Initialize empty profile
        profile = models.UserProfile(user_id=user.id)
        db.add(profile)
        db.commit()

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive")

    # Return access and refresh tokens
    return token_response(user)

@router.get("/me", response_model=schemas.UserOut)
def get_current_user_info(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return current_user
