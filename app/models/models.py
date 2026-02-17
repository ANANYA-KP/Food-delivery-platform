"""
All database models for Food Delivery Platform
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


# ==================== ENUMS ====================

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    RESTAURANT = "restaurant"
    DELIVERY_PARTNER = "delivery_partner"
    ADMIN = "admin"

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    PENDING = "pending"

class RestaurantStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class CuisineType(str, enum.Enum):
    INDIAN = "indian"
    CHINESE = "chinese"
    ITALIAN = "italian"
    MEXICAN = "mexican"
    AMERICAN = "american"
    FAST_FOOD = "fast_food"
    DESSERTS = "desserts"
    BEVERAGES = "beverages"

class FoodCategory(str, enum.Enum):
    STARTER = "starter"
    MAIN_COURSE = "main_course"
    DESSERT = "dessert"
    BEVERAGE = "beverage"
    SNACK = "snack"
    COMBO = "combo"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentMethod(str, enum.Enum):
    UPI = "upi"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    NET_BANKING = "net_banking"
    COD = "cod"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class DeliveryPartnerStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class AvailabilityStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"

class VehicleType(str, enum.Enum):
    BIKE = "bike"
    SCOOTER = "scooter"
    BICYCLE = "bicycle"
    CAR = "car"


# ==================== MODELS ====================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole, native_enum=False), default=UserRole.CUSTOMER)
    status = Column(SQLEnum(UserStatus, native_enum=False), default=UserStatus.ACTIVE)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    otp = Column(String, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    profile_image = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer", foreign_keys="Order.customer_id")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    restaurant = relationship("Restaurant", back_populates="user", uselist=False)
    delivery_partner = relationship("DeliveryPartner", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.email or self.phone}>"


class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String, default="Home")
    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="addresses")
    orders = relationship("Order", back_populates="delivery_address")


class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    cuisine_type = Column(SQLEnum(CuisineType, native_enum=False))
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String)
    pincode = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    logo = Column(String, nullable=True)
    is_veg = Column(Boolean, default=False)
    is_non_veg = Column(Boolean, default=True)
    opening_time = Column(String, default="09:00")
    closing_time = Column(String, default="22:00")
    avg_delivery_time = Column(Integer, default=30)
    rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)
    status = Column(SQLEnum(RestaurantStatus, native_enum=False), default=RestaurantStatus.APPROVED)
    is_active = Column(Boolean, default=True)
    delivery_charge = Column(Float, default=30.0)
    min_order_amount = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="restaurant")
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant")
    ratings = relationship("Rating", back_populates="restaurant")

    def __repr__(self):
        return f"<Restaurant {self.name}>"


class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    category = Column(SQLEnum(FoodCategory, native_enum=False))
    price = Column(Float, nullable=False)
    discount_price = Column(Float, nullable=True)
    is_veg = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    is_recommended = Column(Boolean, default=False)
    image = Column(String, nullable=True)
    calories = Column(Integer, nullable=True)
    preparation_time = Column(Integer, default=15)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item")

    def __repr__(self):
        return f"<MenuItem {self.name}>"


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    delivery_partner_id = Column(Integer, ForeignKey("delivery_partners.id"), nullable=True)
    delivery_address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    status = Column(SQLEnum(OrderStatus, native_enum=False), default=OrderStatus.PENDING)
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    delivery_charge = Column(Float, default=0.0)
    platform_fee = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod, native_enum=False), default=PaymentMethod.COD)
    payment_status = Column(SQLEnum(PaymentStatus, native_enum=False), default=PaymentStatus.PENDING)
    payment_id = Column(String, nullable=True)
    promo_code = Column(String, nullable=True)
    estimated_delivery_time = Column(DateTime, nullable=True)
    actual_delivery_time = Column(DateTime, nullable=True)
    special_instructions = Column(Text, nullable=True)
    cancelled_by = Column(String, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)

    customer = relationship("User", back_populates="orders", foreign_keys=[customer_id])
    restaurant = relationship("Restaurant", back_populates="orders")
    delivery_partner = relationship("DeliveryPartner", back_populates="orders")
    delivery_address = relationship("Address", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    rating = relationship("Rating", back_populates="order", uselist=False)

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    item_name = Column(String, nullable=False)
    item_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)
    special_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="order_items")
    menu_item = relationship("MenuItem", back_populates="order_items")


class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    vehicle_type = Column(SQLEnum(VehicleType, native_enum=False), default=VehicleType.BIKE)
    vehicle_number = Column(String, nullable=False)
    license_number = Column(String, nullable=False)
    status = Column(SQLEnum(DeliveryPartnerStatus, native_enum=False), default=DeliveryPartnerStatus.APPROVED)
    availability_status = Column(SQLEnum(AvailabilityStatus, native_enum=False), default=AvailabilityStatus.OFFLINE)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="delivery_partner")
    orders = relationship("Order", back_populates="delivery_partner")
    ratings = relationship("Rating", back_populates="delivery_partner")

    def __repr__(self):
        return f"<DeliveryPartner {self.vehicle_number}>"


class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    delivery_partner_id = Column(Integer, ForeignKey("delivery_partners.id"), nullable=True)
    restaurant_rating = Column(Integer, nullable=False)
    food_rating = Column(Integer, nullable=False)
    delivery_rating = Column(Integer, nullable=True)
    restaurant_review = Column(Text, nullable=True)
    delivery_review = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ratings")
    restaurant = relationship("Restaurant", back_populates="ratings")
    delivery_partner = relationship("DeliveryPartner", back_populates="ratings")
    order = relationship("Order", back_populates="rating")

    def __repr__(self):
        return f"<Rating Order#{self.order_id}>"
