"""
Reset Database Script
=====================
Deletes the old database and creates fresh demo data.

HOW TO RUN:
    python reset_db.py

Run this BEFORE python main.py if login is not working.
"""
import os
import sys

print()
print("=" * 55)
print("  Food Delivery Platform - Database Reset")
print("=" * 55)

# ── Step 1: Delete old database ──
db_file = "food_delivery.db"
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"\n✅  Deleted old database: {db_file}")
else:
    print(f"\nℹ️   No existing database found, creating fresh one")

# ── Step 2: Create tables ──
print("⏳  Creating database tables...")
from app.core.database import engine, Base
import app.models.models
Base.metadata.create_all(bind=engine)
print("✅  Tables created")

# ── Step 3: Seed data ──
print("⏳  Adding demo data...")

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.models import (
    User, UserRole, UserStatus, Address,
    Restaurant, MenuItem, RestaurantStatus, CuisineType, FoodCategory,
    DeliveryPartner, VehicleType, DeliveryPartnerStatus, AvailabilityStatus
)

db = SessionLocal()

try:
    # ── ADMIN ──
    admin = User(
        email="admin@fooddelivery.com",
        full_name="Admin User",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_email_verified=True
    )
    db.add(admin)

    # ── CUSTOMER ──
    customer = User(
        email="customer@example.com",
        phone="9876543210",
        full_name="Rahul Sharma",
        hashed_password=get_password_hash("customer123"),
        role=UserRole.CUSTOMER,
        status=UserStatus.ACTIVE,
        is_email_verified=True
    )
    db.add(customer)
    db.flush()

    # Customer address (needed for placing orders)
    db.add(Address(
        user_id=customer.id,
        label="Home",
        address_line1="12, Park Street",
        city="Bengaluru",
        state="Karnataka",
        pincode="560001",
        is_default=True
    ))

    # ── RESTAURANT OWNER 1 ──
    owner1 = User(
        email="owner@pizzapalace.com",
        full_name="Priya Patel",
        hashed_password=get_password_hash("owner123"),
        role=UserRole.RESTAURANT,
        status=UserStatus.ACTIVE,
        is_email_verified=True
    )
    db.add(owner1)
    db.flush()

    rest1 = Restaurant(
        user_id=owner1.id,
        name="Pizza Palace",
        description="Best pizzas in town with authentic Italian flavors",
        cuisine_type=CuisineType.ITALIAN,
        phone="9876500001",
        email="owner@pizzapalace.com",
        address="123, MG Road, Bengaluru",
        city="Bengaluru",
        pincode="560001",
        latitude=12.9716, longitude=77.5946,
        is_veg=False, is_non_veg=True,
        opening_time="10:00", closing_time="23:00",
        avg_delivery_time=25,
        rating=4.3, total_ratings=128,
        status=RestaurantStatus.APPROVED,
        is_active=True,
        delivery_charge=30.0,
        min_order_amount=150.0
    )
    db.add(rest1)
    db.flush()

    for m in [
        MenuItem(restaurant_id=rest1.id, name="Margherita Pizza",
                 description="Classic tomato and mozzarella",
                 category=FoodCategory.MAIN_COURSE, price=249.0,
                 is_veg=True, is_available=True, is_recommended=True,
                 calories=650, preparation_time=20),
        MenuItem(restaurant_id=rest1.id, name="Pepperoni Pizza",
                 description="Loaded with pepperoni slices",
                 category=FoodCategory.MAIN_COURSE, price=349.0,
                 is_veg=False, is_available=True, is_recommended=True,
                 calories=820, preparation_time=20),
        MenuItem(restaurant_id=rest1.id, name="Garlic Bread",
                 description="Crispy garlic bread with herbs",
                 category=FoodCategory.STARTER, price=99.0,
                 is_veg=True, is_available=True,
                 calories=280, preparation_time=10),
        MenuItem(restaurant_id=rest1.id, name="Cold Drink",
                 description="Assorted cold beverages",
                 category=FoodCategory.BEVERAGE, price=60.0,
                 is_veg=True, is_available=True,
                 calories=150, preparation_time=2),
    ]:
        db.add(m)

    # ── RESTAURANT OWNER 2 ──
    owner2 = User(
        email="owner@spicehut.com",
        full_name="Amit Verma",
        hashed_password=get_password_hash("owner123"),
        role=UserRole.RESTAURANT,
        status=UserStatus.ACTIVE,
        is_email_verified=True
    )
    db.add(owner2)
    db.flush()

    rest2 = Restaurant(
        user_id=owner2.id,
        name="Spice Hut",
        description="Authentic North Indian cuisine with rich gravies",
        cuisine_type=CuisineType.INDIAN,
        phone="9876500002",
        email="owner@spicehut.com",
        address="45, Indiranagar, Bengaluru",
        city="Bengaluru",
        pincode="560038",
        latitude=12.9784, longitude=77.6408,
        is_veg=True, is_non_veg=True,
        opening_time="11:00", closing_time="22:00",
        avg_delivery_time=30,
        rating=4.6, total_ratings=250,
        status=RestaurantStatus.APPROVED,
        is_active=True,
        delivery_charge=20.0,
        min_order_amount=100.0
    )
    db.add(rest2)
    db.flush()

    for m in [
        MenuItem(restaurant_id=rest2.id, name="Butter Chicken",
                 description="Creamy tomato-based chicken curry",
                 category=FoodCategory.MAIN_COURSE, price=299.0,
                 is_veg=False, is_available=True, is_recommended=True,
                 calories=420, preparation_time=15),
        MenuItem(restaurant_id=rest2.id, name="Paneer Butter Masala",
                 description="Cottage cheese in rich butter gravy",
                 category=FoodCategory.MAIN_COURSE, price=249.0,
                 is_veg=True, is_available=True, is_recommended=True,
                 calories=380, preparation_time=15),
        MenuItem(restaurant_id=rest2.id, name="Dal Makhani",
                 description="Slow cooked black lentils",
                 category=FoodCategory.MAIN_COURSE, price=199.0,
                 is_veg=True, is_available=True,
                 calories=310, preparation_time=10),
        MenuItem(restaurant_id=rest2.id, name="Garlic Naan",
                 description="Freshly baked garlic naan",
                 category=FoodCategory.STARTER, price=49.0,
                 is_veg=True, is_available=True,
                 calories=120, preparation_time=5),
        MenuItem(restaurant_id=rest2.id, name="Gulab Jamun",
                 description="Sweet milk dumplings in sugar syrup",
                 category=FoodCategory.DESSERT, price=79.0,
                 is_veg=True, is_available=True,
                 calories=280, preparation_time=3),
    ]:
        db.add(m)

    # ── DELIVERY PARTNER ──
    rider = User(
        email="rider@example.com",
        phone="9876500099",
        full_name="Suresh Kumar",
        hashed_password=get_password_hash("rider123"),
        role=UserRole.DELIVERY_PARTNER,
        status=UserStatus.ACTIVE
    )
    db.add(rider)
    db.flush()

    db.add(DeliveryPartner(
        user_id=rider.id,
        vehicle_type=VehicleType.BIKE,
        vehicle_number="KA01AB1234",
        license_number="DL-2019-0112345",
        status=DeliveryPartnerStatus.APPROVED,
        availability_status=AvailabilityStatus.ONLINE,
        current_latitude=12.9716, current_longitude=77.5946,
        total_deliveries=145, successful_deliveries=140,
        rating=4.7, total_ratings=92, total_earnings=14500.0
    ))

    db.commit()

    print()
    print("=" * 55)
    print("  ✅  DATABASE RESET COMPLETE!")
    print("=" * 55)
    print()
    print("  🔑  LOGIN CREDENTIALS:")
    print()
    print("  Role        Email                       Password")
    print("  ─────────────────────────────────────────────────")
    print("  Admin       admin@fooddelivery.com      admin123")
    print("  Customer    customer@example.com        customer123")
    print("  Restaurant  owner@pizzapalace.com       owner123")
    print("  Delivery    rider@example.com           rider123")
    print("  ─────────────────────────────────────────────────")
    print()
    print("  🚀  Next step: python main.py")
    print("  🌐  Then open: http://localhost:8000/docs")
    print()

except Exception as e:
    db.rollback()
    print(f"\n❌  ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
