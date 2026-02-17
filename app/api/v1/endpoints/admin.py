"""
Admin dashboard endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.models import (
    User, Restaurant, Order, DeliveryPartner, Rating,
    UserRole, UserStatus, RestaurantStatus, OrderStatus, PaymentStatus
)
from app.schemas.schemas import UserResponse, RestaurantResponse

router = APIRouter()

def require_admin_role(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/dashboard")
async def admin_dashboard(
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Admin overview dashboard with key metrics"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    this_month = today.replace(day=1)

    total_users = db.query(func.count(User.id)).scalar()
    total_restaurants = db.query(func.count(Restaurant.id)).scalar()
    total_orders = db.query(func.count(Order.id)).scalar()
    total_partners = db.query(func.count(DeliveryPartner.id)).scalar()

    today_orders = db.query(func.count(Order.id)).filter(Order.created_at >= today).scalar()
    today_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= today,
        Order.payment_status == PaymentStatus.COMPLETED
    ).scalar() or 0.0

    monthly_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= this_month,
        Order.payment_status == PaymentStatus.COMPLETED
    ).scalar() or 0.0

    active_orders = db.query(func.count(Order.id)).filter(
        Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.PICKED_UP, OrderStatus.OUT_FOR_DELIVERY])
    ).scalar()

    pending_restaurants = db.query(func.count(Restaurant.id)).filter(
        Restaurant.status == RestaurantStatus.PENDING
    ).scalar()

    return {
        "stats": {
            "total_users": total_users,
            "total_restaurants": total_restaurants,
            "total_orders": total_orders,
            "total_delivery_partners": total_partners,
            "today_orders": today_orders,
            "today_revenue": round(today_revenue, 2),
            "monthly_revenue": round(monthly_revenue, 2),
            "active_orders": active_orders,
            "pending_restaurant_approvals": pending_restaurants,
        }
    }


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    role: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """List all users"""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)
    return query.offset(skip).limit(limit).all()


@router.patch("/users/{user_id}/block")
async def block_user(
    user_id: int,
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Block a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = UserStatus.BLOCKED
    db.commit()
    return {"message": f"User {user.full_name} has been blocked"}


@router.patch("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Unblock a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = UserStatus.ACTIVE
    db.commit()
    return {"message": f"User {user.full_name} has been unblocked"}


@router.get("/restaurants", response_model=List[RestaurantResponse])
async def list_all_restaurants(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """List all restaurants"""
    query = db.query(Restaurant)
    if status:
        query = query.filter(Restaurant.status == status)
    return query.offset(skip).limit(limit).all()


@router.patch("/restaurants/{restaurant_id}/approve")
async def approve_restaurant(
    restaurant_id: int,
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Approve a restaurant"""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    restaurant.status = RestaurantStatus.APPROVED
    db.commit()
    return {"message": f"Restaurant '{restaurant.name}' has been approved"}


@router.patch("/restaurants/{restaurant_id}/suspend")
async def suspend_restaurant(
    restaurant_id: int,
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Suspend a restaurant"""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    restaurant.status = RestaurantStatus.SUSPENDED
    db.commit()
    return {"message": f"Restaurant '{restaurant.name}' has been suspended"}


@router.get("/orders")
async def list_all_orders(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """List all orders"""
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/reports/revenue")
async def revenue_report(
    period: str = "daily",
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Revenue reports - daily or monthly"""
    if period == "daily":
        days = 30
        results = []
        for i in range(days):
            day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            next_day = day + timedelta(days=1)
            revenue = db.query(func.sum(Order.total_amount)).filter(
                Order.created_at >= day,
                Order.created_at < next_day,
                Order.payment_status == PaymentStatus.COMPLETED
            ).scalar() or 0.0
            orders_count = db.query(func.count(Order.id)).filter(
                Order.created_at >= day,
                Order.created_at < next_day
            ).scalar()
            results.append({"date": day.strftime("%Y-%m-%d"), "revenue": round(revenue, 2), "orders": orders_count})
        return {"period": "daily", "data": results[::-1]}

    elif period == "monthly":
        results = []
        for i in range(12):
            month_date = (datetime.utcnow().replace(day=1) - timedelta(days=i * 30)).replace(day=1)
            next_month = (month_date + timedelta(days=32)).replace(day=1)
            revenue = db.query(func.sum(Order.total_amount)).filter(
                Order.created_at >= month_date,
                Order.created_at < next_month,
                Order.payment_status == PaymentStatus.COMPLETED
            ).scalar() or 0.0
            orders_count = db.query(func.count(Order.id)).filter(
                Order.created_at >= month_date,
                Order.created_at < next_month
            ).scalar()
            results.append({"month": month_date.strftime("%Y-%m"), "revenue": round(revenue, 2), "orders": orders_count})
        return {"period": "monthly", "data": results[::-1]}


@router.get("/reports/restaurants")
async def restaurant_performance(
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Restaurant performance report"""
    restaurants = db.query(Restaurant).all()
    report = []
    for r in restaurants:
        order_count = db.query(func.count(Order.id)).filter(Order.restaurant_id == r.id).scalar()
        revenue = db.query(func.sum(Order.total_amount)).filter(
            Order.restaurant_id == r.id,
            Order.payment_status == PaymentStatus.COMPLETED
        ).scalar() or 0.0
        report.append({
            "restaurant_id": r.id,
            "name": r.name,
            "rating": r.rating,
            "total_orders": order_count,
            "total_revenue": round(revenue, 2),
            "status": r.status
        })
    return {"restaurants": sorted(report, key=lambda x: x["total_revenue"], reverse=True)}
