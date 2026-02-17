"""
Restaurant and Menu management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.deps import get_current_active_user, require_restaurant, require_admin
from app.models.models import Restaurant, MenuItem, User, UserRole, RestaurantStatus, CuisineType
from app.schemas.schemas import (
    RestaurantCreate, RestaurantUpdate, RestaurantResponse,
    MenuItemCreate, MenuItemUpdate, MenuItemResponse
)

router = APIRouter()


# ==================== RESTAURANT ENDPOINTS ====================

@router.get("/", response_model=List[RestaurantResponse])
async def list_restaurants(
    cuisine: Optional[str] = None,
    min_rating: Optional[float] = None,
    is_veg: Optional[bool] = None,
    city: Optional[str] = None,
    sort_by: str = "rating",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Browse all active, approved restaurants with filters"""
    query = db.query(Restaurant).filter(
        Restaurant.is_active == True,
        Restaurant.status == RestaurantStatus.APPROVED
    )
    if cuisine:
        query = query.filter(Restaurant.cuisine_type == cuisine)
    if min_rating:
        query = query.filter(Restaurant.rating >= min_rating)
    if is_veg is True:
        query = query.filter(Restaurant.is_veg == True)
    if city:
        query = query.filter(Restaurant.city.ilike(f"%{city}%"))
    if sort_by == "rating":
        query = query.order_by(Restaurant.rating.desc())
    elif sort_by == "delivery_time":
        query = query.order_by(Restaurant.avg_delivery_time.asc())
    return query.offset(skip).limit(limit).all()


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """Get restaurant details"""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.post("/", response_model=RestaurantResponse, status_code=201)
async def create_restaurant(
    data: RestaurantCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Register a new restaurant (requires restaurant role)"""
    if current_user.role not in [UserRole.RESTAURANT, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only restaurant owners can register restaurants")
    if db.query(Restaurant).filter(Restaurant.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="You already have a registered restaurant")

    restaurant = Restaurant(**data.model_dump(), user_id=current_user.id)
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: int,
    data: RestaurantUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update restaurant details"""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(restaurant, field, value)
    db.commit()
    db.refresh(restaurant)
    return restaurant


# ==================== MENU ENDPOINTS ====================

@router.get("/{restaurant_id}/menu", response_model=List[MenuItemResponse])
async def get_menu(
    restaurant_id: int,
    category: Optional[str] = None,
    is_veg: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get restaurant menu"""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    query = db.query(MenuItem).filter(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.is_available == True
    )
    if category:
        query = query.filter(MenuItem.category == category)
    if is_veg is not None:
        query = query.filter(MenuItem.is_veg == is_veg)
    return query.all()


@router.post("/{restaurant_id}/menu", response_model=MenuItemResponse, status_code=201)
async def add_menu_item(
    restaurant_id: int,
    data: MenuItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add menu item"""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    item = MenuItem(**data.model_dump(), restaurant_id=restaurant_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{restaurant_id}/menu/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    restaurant_id: int,
    item_id: int,
    data: MenuItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update menu item"""
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if restaurant.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{restaurant_id}/menu/{item_id}")
async def delete_menu_item(
    restaurant_id: int,
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete menu item"""
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if restaurant.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(item)
    db.commit()
    return {"message": "Menu item deleted"}
