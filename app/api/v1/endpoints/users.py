"""
User profile, delivery partner, and ratings endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.models import (
    User, Address, DeliveryPartner, Rating, Order, Restaurant,
    UserRole, OrderStatus, DeliveryPartnerStatus, AvailabilityStatus
)
from app.schemas.schemas import (
    AddressCreate, AddressResponse, UserUpdate, UserResponse,
    DeliveryPartnerCreate, DeliveryPartnerUpdate, DeliveryPartnerResponse,
    RatingCreate, RatingResponse
)

# ========== USER ROUTER ===========
users_router = APIRouter()

@users_router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user

@users_router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user

@users_router.get("/addresses", response_model=List[AddressResponse])
async def get_addresses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all addresses for current user"""
    return db.query(Address).filter(Address.user_id == current_user.id).all()

@users_router.post("/addresses", response_model=AddressResponse, status_code=201)
async def add_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a new delivery address"""
    if data.is_default:
        # Remove existing default
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})
    address = Address(**data.model_dump(), user_id=current_user.id)
    db.add(address)
    db.commit()
    db.refresh(address)
    return address

@users_router.delete("/addresses/{address_id}")
async def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an address"""
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(address)
    db.commit()
    return {"message": "Address deleted"}


# ========== DELIVERY PARTNER ROUTER ===========
delivery_router = APIRouter()

@delivery_router.post("/register", response_model=DeliveryPartnerResponse, status_code=201)
async def register_delivery_partner(
    data: DeliveryPartnerCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Register as delivery partner"""
    if db.query(DeliveryPartner).filter(DeliveryPartner.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Already registered as delivery partner")
    partner = DeliveryPartner(**data.model_dump(), user_id=current_user.id)
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner

@delivery_router.get("/profile", response_model=DeliveryPartnerResponse)
async def get_delivery_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get delivery partner profile"""
    partner = db.query(DeliveryPartner).filter(DeliveryPartner.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Not registered as delivery partner")
    return partner

@delivery_router.put("/status")
async def update_availability(
    data: DeliveryPartnerUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update delivery partner availability and location"""
    partner = db.query(DeliveryPartner).filter(DeliveryPartner.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Not registered as delivery partner")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(partner, field, value)
    if data.current_latitude or data.current_longitude:
        partner.last_location_update = datetime.utcnow()
    db.commit()
    db.refresh(partner)
    return {"message": "Status updated", "availability": partner.availability_status}

@delivery_router.get("/my-deliveries")
async def get_my_deliveries(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get assigned deliveries"""
    partner = db.query(DeliveryPartner).filter(DeliveryPartner.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Not registered as delivery partner")
    orders = db.query(Order).filter(Order.delivery_partner_id == partner.id).order_by(Order.created_at.desc()).limit(20).all()
    return orders


# ========== RATINGS ROUTER ===========
ratings_router = APIRouter()

@ratings_router.post("/", response_model=RatingResponse, status_code=201)
async def submit_rating(
    data: RatingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit a rating for an order"""
    order = db.query(Order).filter(Order.id == data.order_id, Order.customer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(status_code=400, detail="Can only rate delivered orders")
    if db.query(Rating).filter(Rating.order_id == data.order_id).first():
        raise HTTPException(status_code=400, detail="Already rated this order")

    rating = Rating(
        order_id=data.order_id,
        user_id=current_user.id,
        restaurant_id=order.restaurant_id,
        delivery_partner_id=order.delivery_partner_id,
        **data.model_dump(exclude={"order_id"})
    )
    db.add(rating)

    # Update restaurant average rating
    restaurant = db.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()
    if restaurant:
        total = restaurant.rating * restaurant.total_ratings + data.restaurant_rating
        restaurant.total_ratings += 1
        restaurant.rating = round(total / restaurant.total_ratings, 2)

    # Update delivery partner rating
    if order.delivery_partner_id and data.delivery_rating:
        partner = db.query(DeliveryPartner).filter(DeliveryPartner.id == order.delivery_partner_id).first()
        if partner:
            total = partner.rating * partner.total_ratings + data.delivery_rating
            partner.total_ratings += 1
            partner.rating = round(total / partner.total_ratings, 2)

    db.commit()
    db.refresh(rating)
    return rating

@ratings_router.get("/restaurant/{restaurant_id}", response_model=List[RatingResponse])
async def get_restaurant_ratings(
    restaurant_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get ratings for a restaurant"""
    return db.query(Rating).filter(Rating.restaurant_id == restaurant_id).offset(skip).limit(limit).all()
