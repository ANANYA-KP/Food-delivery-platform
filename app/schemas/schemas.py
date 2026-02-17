"""
Pydantic schemas for all API endpoints
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.models import (
    UserRole, UserStatus, RestaurantStatus, CuisineType,
    FoodCategory, OrderStatus, PaymentMethod, PaymentStatus,
    DeliveryPartnerStatus, AvailabilityStatus, VehicleType
)


# ==================== USER SCHEMAS ====================

class UserRegister(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.CUSTOMER

class UserLogin(BaseModel):
    email_or_phone: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: Optional[str]
    phone: Optional[str]
    full_name: str
    role: UserRole
    status: UserStatus
    is_email_verified: bool
    is_phone_verified: bool
    profile_image: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    otp: str

class PasswordReset(BaseModel):
    email: EmailStr

class RefreshToken(BaseModel):
    refresh_token: str


# ==================== ADDRESS SCHEMAS ====================

class AddressCreate(BaseModel):
    label: str = "Home"
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False

class AddressResponse(AddressCreate):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== RESTAURANT SCHEMAS ====================

class RestaurantCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cuisine_type: CuisineType
    phone: str
    email: EmailStr
    address: str
    city: str
    pincode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_veg: bool = False
    is_non_veg: bool = True
    opening_time: str = "09:00"
    closing_time: str = "22:00"
    avg_delivery_time: int = 30
    delivery_charge: float = 30.0
    min_order_amount: float = 100.0

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cuisine_type: Optional[CuisineType] = None
    phone: Optional[str] = None
    is_veg: Optional[bool] = None
    is_non_veg: Optional[bool] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    avg_delivery_time: Optional[int] = None
    delivery_charge: Optional[float] = None
    min_order_amount: Optional[float] = None
    is_active: Optional[bool] = None

class RestaurantResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    cuisine_type: Optional[CuisineType]
    phone: str
    email: str
    address: str
    city: Optional[str]
    pincode: Optional[str]
    is_veg: bool
    is_non_veg: bool
    opening_time: Optional[str]
    closing_time: Optional[str]
    avg_delivery_time: int
    rating: float
    total_ratings: int
    status: RestaurantStatus
    is_active: bool
    delivery_charge: float
    min_order_amount: float
    logo: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== MENU SCHEMAS ====================

class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: FoodCategory
    price: float
    discount_price: Optional[float] = None
    is_veg: bool = True
    is_available: bool = True
    is_recommended: bool = False
    calories: Optional[int] = None
    preparation_time: int = 15

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[FoodCategory] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    is_veg: Optional[bool] = None
    is_available: Optional[bool] = None
    is_recommended: Optional[bool] = None

class MenuItemResponse(BaseModel):
    id: int
    restaurant_id: int
    name: str
    description: Optional[str]
    category: Optional[FoodCategory]
    price: float
    discount_price: Optional[float]
    is_veg: bool
    is_available: bool
    is_recommended: bool
    calories: Optional[int]
    preparation_time: int
    image: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== ORDER SCHEMAS ====================

class CartItem(BaseModel):
    menu_item_id: int
    quantity: int = Field(..., ge=1)
    special_instructions: Optional[str] = None

class OrderCreate(BaseModel):
    restaurant_id: int
    delivery_address_id: int
    items: List[CartItem]
    payment_method: PaymentMethod = PaymentMethod.COD
    promo_code: Optional[str] = None
    special_instructions: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    item_name: str
    item_price: float
    quantity: int
    subtotal: float
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_id: int
    restaurant_id: int
    delivery_partner_id: Optional[int]
    status: OrderStatus
    subtotal: float
    tax_amount: float
    delivery_charge: float
    platform_fee: float
    discount_amount: float
    total_amount: float
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    promo_code: Optional[str]
    special_instructions: Optional[str]
    estimated_delivery_time: Optional[datetime]
    actual_delivery_time: Optional[datetime]
    order_items: List[OrderItemResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== DELIVERY SCHEMAS ====================

class DeliveryPartnerCreate(BaseModel):
    vehicle_type: VehicleType
    vehicle_number: str
    license_number: str

class DeliveryPartnerUpdate(BaseModel):
    vehicle_type: Optional[VehicleType] = None
    vehicle_number: Optional[str] = None
    availability_status: Optional[AvailabilityStatus] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None

class DeliveryPartnerResponse(BaseModel):
    id: int
    user_id: int
    vehicle_type: Optional[VehicleType]
    vehicle_number: str
    license_number: str
    status: DeliveryPartnerStatus
    availability_status: AvailabilityStatus
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    total_deliveries: int
    successful_deliveries: int
    rating: float
    total_earnings: float
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== RATING SCHEMAS ====================

class RatingCreate(BaseModel):
    order_id: int
    restaurant_rating: int = Field(..., ge=1, le=5)
    food_rating: int = Field(..., ge=1, le=5)
    delivery_rating: Optional[int] = Field(None, ge=1, le=5)
    restaurant_review: Optional[str] = None
    delivery_review: Optional[str] = None

class RatingResponse(BaseModel):
    id: int
    order_id: int
    restaurant_rating: int
    food_rating: int
    delivery_rating: Optional[int]
    restaurant_review: Optional[str]
    delivery_review: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
