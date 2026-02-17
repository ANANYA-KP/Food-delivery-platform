"""
API Dependencies - Authentication and Authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_token
from app.models.models import User, UserRole, UserStatus

security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(credentials.credentials)
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.status == UserStatus.BLOCKED:
        raise HTTPException(status_code=403, detail="Account is blocked")
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Account not active")
    return current_user

def require_role(*roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

require_admin = require_role(UserRole.ADMIN)
require_restaurant = require_role(UserRole.RESTAURANT, UserRole.ADMIN)
require_delivery = require_role(UserRole.DELIVERY_PARTNER, UserRole.ADMIN)
require_customer = require_role(UserRole.CUSTOMER, UserRole.ADMIN)
