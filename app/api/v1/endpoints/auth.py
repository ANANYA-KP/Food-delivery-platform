"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from app.models.models import User, UserStatus, UserRole
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, OTPRequest, OTPVerify, PasswordReset, RefreshToken

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)

def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    if user_data.email:
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
    if user_data.phone:
        if db.query(User).filter(User.phone == user_data.phone).first():
            raise HTTPException(status_code=400, detail="Phone already registered")
    if not user_data.email and not user_data.phone:
        raise HTTPException(status_code=400, detail="Email or phone required")

    new_user = User(
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        status=UserStatus.ACTIVE,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(data={"sub": str(new_user.id), "role": new_user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user": new_user}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with email/phone and password"""
    user = db.query(User).filter(
        (User.email == credentials.email_or_phone) |
        (User.phone == credentials.email_or_phone)
    ).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.status == UserStatus.BLOCKED:
        raise HTTPException(status_code=403, detail="Account is blocked")

    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user": user}


@router.post("/request-otp")
async def request_otp(otp_request: OTPRequest, db: Session = Depends(get_db)):
    """Request OTP for phone verification"""
    otp = generate_otp()
    otp_expiry = datetime.utcnow() + timedelta(minutes=5)

    user = db.query(User).filter(User.phone == otp_request.phone).first()
    if not user:
        user = User(phone=otp_request.phone, full_name="", status=UserStatus.PENDING, otp=otp, otp_expiry=otp_expiry)
        db.add(user)
    else:
        user.otp = otp
        user.otp_expiry = otp_expiry
    db.commit()

    # In production: send via Twilio/MSG91
    return {"message": "OTP sent successfully", "otp": otp, "note": "OTP shown for demo only"}


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(otp_verify: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP"""
    user = db.query(User).filter(User.phone == otp_verify.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="Phone number not found")
    if user.otp != otp_verify.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if user.otp_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    user.is_phone_verified = True
    user.status = UserStatus.ACTIVE
    user.otp = None
    user.otp_expiry = None
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user": user}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(token_data: RefreshToken, db: Session = Depends(get_db)):
    """Refresh access token"""
    payload = verify_token(token_data.refresh_token, token_type="refresh")
    user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user": user}


@router.get("/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Get current user info"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(credentials.credentials)
    user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


