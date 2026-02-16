"""
Food Delivery Platform - Main Application
Run with: python main.py
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_tables():
    from app.core.database import engine, Base
    import app.models.models
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables ready")


def seed_demo_data():
    from app.core.database import SessionLocal
    from app.core.security import get_password_hash
    from app.models.models import (
        User, UserRole, UserStatus, Address,
        Restaurant, MenuItem, RestaurantStatus, CuisineType, FoodCategory,
        DeliveryPartner, VehicleType, DeliveryPartnerStatus, AvailabilityStatus
    )
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "admin@fooddelivery.com").first():
            logger.info("✅ Demo data already exists")
            return

        logger.info("🌱 Seeding demo data...")

        # ADMIN
        admin = User(email="admin@fooddelivery.com", full_name="Admin User",
                     hashed_password=get_password_hash("admin123"),
                     role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_email_verified=True)
        db.add(admin)

        # CUSTOMER
        customer = User(email="customer@example.com", phone="9876543210",
                        full_name="Rahul Sharma",
                        hashed_password=get_password_hash("customer123"),
                        role=UserRole.CUSTOMER, status=UserStatus.ACTIVE, is_email_verified=True)
        db.add(customer)
        db.flush()

        db.add(Address(user_id=customer.id, label="Home",
                       address_line1="12, Park Street", city="Bengaluru",
                       state="Karnataka", pincode="560001", is_default=True))

        # RESTAURANT OWNER 1
        owner1 = User(email="owner@pizzapalace.com", full_name="Priya Patel",
                      hashed_password=get_password_hash("owner123"),
                      role=UserRole.RESTAURANT, status=UserStatus.ACTIVE, is_email_verified=True)
        db.add(owner1)
        db.flush()

        rest1 = Restaurant(user_id=owner1.id, name="Pizza Palace",
                           description="Best pizzas in town with authentic Italian flavors",
                           cuisine_type=CuisineType.ITALIAN, phone="9876500001",
                           email="owner@pizzapalace.com", address="123, MG Road, Bengaluru",
                           city="Bengaluru", pincode="560001", latitude=12.9716, longitude=77.5946,
                           is_veg=False, is_non_veg=True, opening_time="10:00", closing_time="23:00",
                           avg_delivery_time=25, rating=4.3, total_ratings=128,
                           status=RestaurantStatus.APPROVED, is_active=True,
                           delivery_charge=30.0, min_order_amount=150.0)
        db.add(rest1)
        db.flush()

        for m in [
            MenuItem(restaurant_id=rest1.id, name="Margherita Pizza",
                     description="Classic tomato and mozzarella",
                     category=FoodCategory.MAIN_COURSE, price=249.0,
                     is_veg=True, is_available=True, is_recommended=True, calories=650, preparation_time=20),
            MenuItem(restaurant_id=rest1.id, name="Pepperoni Pizza",
                     description="Loaded with pepperoni slices",
                     category=FoodCategory.MAIN_COURSE, price=349.0,
                     is_veg=False, is_available=True, is_recommended=True, calories=820, preparation_time=20),
            MenuItem(restaurant_id=rest1.id, name="Garlic Bread",
                     description="Crispy garlic bread with herbs",
                     category=FoodCategory.STARTER, price=99.0,
                     is_veg=True, is_available=True, calories=280, preparation_time=10),
            MenuItem(restaurant_id=rest1.id, name="Cold Drink",
                     description="Assorted cold beverages",
                     category=FoodCategory.BEVERAGE, price=60.0,
                     is_veg=True, is_available=True, calories=150, preparation_time=2),
        ]:
            db.add(m)

        # RESTAURANT OWNER 2
        owner2 = User(email="owner@spicehut.com", full_name="Amit Verma",
                      hashed_password=get_password_hash("owner123"),
                      role=UserRole.RESTAURANT, status=UserStatus.ACTIVE, is_email_verified=True)
        db.add(owner2)
        db.flush()

        rest2 = Restaurant(user_id=owner2.id, name="Spice Hut",
                           description="Authentic North Indian cuisine with rich gravies",
                           cuisine_type=CuisineType.INDIAN, phone="9876500002",
                           email="owner@spicehut.com", address="45, Indiranagar, Bengaluru",
                           city="Bengaluru", pincode="560038", latitude=12.9784, longitude=77.6408,
                           is_veg=True, is_non_veg=True, opening_time="11:00", closing_time="22:00",
                           avg_delivery_time=30, rating=4.6, total_ratings=250,
                           status=RestaurantStatus.APPROVED, is_active=True,
                           delivery_charge=20.0, min_order_amount=100.0)
        db.add(rest2)
        db.flush()

        for m in [
            MenuItem(restaurant_id=rest2.id, name="Butter Chicken",
                     description="Creamy tomato-based chicken curry",
                     category=FoodCategory.MAIN_COURSE, price=299.0,
                     is_veg=False, is_available=True, is_recommended=True, calories=420, preparation_time=15),
            MenuItem(restaurant_id=rest2.id, name="Paneer Butter Masala",
                     description="Cottage cheese in rich butter gravy",
                     category=FoodCategory.MAIN_COURSE, price=249.0,
                     is_veg=True, is_available=True, is_recommended=True, calories=380, preparation_time=15),
            MenuItem(restaurant_id=rest2.id, name="Dal Makhani",
                     description="Slow cooked black lentils",
                     category=FoodCategory.MAIN_COURSE, price=199.0,
                     is_veg=True, is_available=True, calories=310, preparation_time=10),
            MenuItem(restaurant_id=rest2.id, name="Garlic Naan",
                     description="Freshly baked garlic naan",
                     category=FoodCategory.STARTER, price=49.0,
                     is_veg=True, is_available=True, calories=120, preparation_time=5),
            MenuItem(restaurant_id=rest2.id, name="Gulab Jamun",
                     description="Sweet milk dumplings in sugar syrup",
                     category=FoodCategory.DESSERT, price=79.0,
                     is_veg=True, is_available=True, calories=280, preparation_time=3),
        ]:
            db.add(m)

        # DELIVERY PARTNER
        rider = User(email="rider@example.com", phone="9876500099",
                     full_name="Suresh Kumar",
                     hashed_password=get_password_hash("rider123"),
                     role=UserRole.DELIVERY_PARTNER, status=UserStatus.ACTIVE)
        db.add(rider)
        db.flush()

        db.add(DeliveryPartner(
            user_id=rider.id, vehicle_type=VehicleType.BIKE,
            vehicle_number="KA01AB1234", license_number="DL-2019-0112345",
            status=DeliveryPartnerStatus.APPROVED,
            availability_status=AvailabilityStatus.ONLINE,
            current_latitude=12.9716, current_longitude=77.5946,
            total_deliveries=145, successful_deliveries=140,
            rating=4.7, total_ratings=92, total_earnings=14500.0
        ))

        db.commit()
        logger.info("✅ Demo data seeded!")
        logger.info("=" * 55)
        logger.info("🔑  DEMO LOGIN CREDENTIALS")
        logger.info("=" * 55)
        logger.info("  Admin      admin@fooddelivery.com   / admin123")
        logger.info("  Customer   customer@example.com     / customer123")
        logger.info("  Restaurant owner@pizzapalace.com    / owner123")
        logger.info("  Delivery   rider@example.com        / rider123")
        logger.info("=" * 55)

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Seed failed: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    seed_demo_data()
    logger.info("🚀  Server ready!")
    logger.info("👉  Open http://localhost:8000/docs")
    yield


app = FastAPI(
    title="🍕 Food Delivery Platform",
    version="1.0.0",
    description="""
## Food Delivery Platform API

### Quick Start
1. Use **POST /api/v1/auth/login** with email + password below
2. Copy `access_token` from response
3. Click **Authorize** → paste `Bearer <token>`

### Demo Credentials
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@fooddelivery.com | admin123 |
| Customer | customer@example.com | customer123 |
| Restaurant | owner@pizzapalace.com | owner123 |
| Delivery | rider@example.com | rider123 |
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

from app.api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")


@app.get("/_old_home", response_class=HTMLResponse)
async def homepage_old():
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Food Delivery Platform</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Segoe UI',sans-serif;background:#f8f9fa}
        .hero{background:linear-gradient(135deg,#FF6B35,#F7C59F);padding:60px 20px;text-align:center;color:#fff}
        .hero h1{font-size:3em;margin-bottom:10px}
        .hero p{font-size:1.2em;opacity:.9;margin-bottom:30px}
        .btns{display:flex;gap:15px;justify-content:center;flex-wrap:wrap}
        .btn{padding:14px 30px;border-radius:8px;text-decoration:none;font-weight:bold}
        .btn-w{background:#fff;color:#FF6B35}
        .btn-o{background:rgba(255,255,255,.2);color:#fff;border:2px solid #fff}
        .wrap{max-width:1100px;margin:0 auto;padding:50px 20px}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;margin:40px 0}
        .card{background:#fff;border-radius:12px;padding:28px;box-shadow:0 4px 20px rgba(0,0,0,.08);text-align:center}
        .card .i{font-size:2.5em;margin-bottom:12px}
        .card h3{color:#333;margin-bottom:8px}
        .card p{color:#666;font-size:.9em;line-height:1.6}
        .box{background:#fff;border-radius:12px;padding:30px;box-shadow:0 4px 20px rgba(0,0,0,.08)}
        table{width:100%;border-collapse:collapse}
        th,td{padding:12px 15px;text-align:left;border-bottom:1px solid #f0f0f0}
        th{background:#FF6B35;color:#fff}
        code{background:#f0f0f0;padding:2px 8px;border-radius:4px;font-family:monospace}
        footer{text-align:center;padding:25px;background:#333;color:#aaa}
    </style>
</head>
<body>
<div class="hero">
    <h1>🍕 Food Delivery Platform</h1>
    <p>Complete Online Food Ordering System — FastAPI + Python</p>
    <div class="btns">
        <a href="/docs" class="btn btn-w">📖 API Docs</a>
        <a href="/redoc" class="btn btn-o">📋 ReDoc</a>
        <a href="/api/v1/restaurants/" class="btn btn-o">🍽️ Restaurants</a>
    </div>
</div>
<div class="wrap">
    <div class="grid">
        <div class="card"><div class="i">🔐</div><h3>Authentication</h3><p>JWT login, register, OTP</p></div>
        <div class="card"><div class="i">👤</div><h3>Customer</h3><p>Profile, addresses, browse restaurants</p></div>
        <div class="card"><div class="i">🍽️</div><h3>Restaurant</h3><p>Menu CRUD, order management</p></div>
        <div class="card"><div class="i">📦</div><h3>Orders</h3><p>Place, track, cancel orders</p></div>
        <div class="card"><div class="i">🛵</div><h3>Delivery</h3><p>GPS tracking, status updates</p></div>
        <div class="card"><div class="i">🔧</div><h3>Admin</h3><p>Dashboard, reports, approvals</p></div>
    </div>
    <div class="box">
        <h2 style="margin-bottom:20px;color:#333">🔑 Demo Login Credentials</h2>
        <table>
            <tr><th>Role</th><th>Email</th><th>Password</th></tr>
            <tr><td>🔧 Admin</td><td><code>admin@fooddelivery.com</code></td><td><code>admin123</code></td></tr>
            <tr><td>👤 Customer</td><td><code>customer@example.com</code></td><td><code>customer123</code></td></tr>
            <tr><td>🍽️ Restaurant</td><td><code>owner@pizzapalace.com</code></td><td><code>owner123</code></td></tr>
            <tr><td>🛵 Delivery</td><td><code>rider@example.com</code></td><td><code>rider123</code></td></tr>
        </table>
        <p style="margin-top:15px;color:#666;font-size:.9em">
            👉 Go to <a href="/docs" style="color:#FF6B35">/docs</a> → POST /api/v1/auth/login → Try it out → copy token → Authorize
        </p>
    </div>
</div>
<footer>Food Delivery Platform v1.0 • FastAPI + SQLite • Python 🐍</footer>
</body>
</html>
""")


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

# ── WEB PAGE ROUTES ──
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# ── WEB PAGE ROUTES ──
from fastapi.templating import Jinja2Templates
from fastapi import Request, Depends
from app.core.database import get_db as _get_db

templates = Jinja2Templates(directory="templates")

@app.get("/restaurants", response_class=HTMLResponse)
async def web_restaurants(request: Request, db=Depends(_get_db)):
    from app.models.models import Restaurant, RestaurantStatus
    restaurants = db.query(Restaurant).filter(
        Restaurant.is_active == True,
        Restaurant.status == RestaurantStatus.APPROVED
    ).order_by(Restaurant.rating.desc()).all()
    return templates.TemplateResponse("restaurants.html", {"request": request, "restaurants": restaurants})

@app.get("/restaurant/{restaurant_id}", response_class=HTMLResponse)
async def web_restaurant_detail(request: Request, restaurant_id: int, db=Depends(_get_db)):
    from app.models.models import Restaurant, MenuItem
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        return HTMLResponse("<h1>Restaurant not found</h1>", status_code=404)
    menu_items = db.query(MenuItem).filter(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.is_available == True
    ).all()
    menu_by_category = {}
    for item in menu_items:
        cat = item.category.value if item.category else "other"
        menu_by_category.setdefault(cat, []).append(item)
    return templates.TemplateResponse("restaurant_detail.html", {
        "request": request,
        "restaurant": restaurant,
        "menu_by_category": menu_by_category
    })

@app.get("/checkout", response_class=HTMLResponse)
async def web_checkout(request: Request):
    return templates.TemplateResponse("checkout.html", {"request": request})

@app.get("/orders", response_class=HTMLResponse)
async def web_orders_page(request: Request):
    return templates.TemplateResponse("orders.html", {"request": request})

@app.get("/order/{order_id}", response_class=HTMLResponse)
async def web_order_detail(request: Request, order_id: int):
    return templates.TemplateResponse("order_detail.html", {"request": request, "order_id": order_id})

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db=Depends(_get_db)):
    from app.models.models import Restaurant, RestaurantStatus
    restaurants = db.query(Restaurant).filter(
        Restaurant.is_active == True,
        Restaurant.status == RestaurantStatus.APPROVED
    ).order_by(Restaurant.rating.desc()).limit(6).all()
    cuisines = [
        {"value": "indian",    "label": "Indian",    "icon": "🍛"},
        {"value": "italian",   "label": "Italian",   "icon": "🍕"},
        {"value": "chinese",   "label": "Chinese",   "icon": "🥡"},
        {"value": "american",  "label": "American",  "icon": "🍔"},
        {"value": "fast_food", "label": "Fast Food", "icon": "🌮"},
        {"value": "desserts",  "label": "Desserts",  "icon": "🍰"},
    ]
    # Add emoji to restaurants
    emoji_map = {"italian":"🍕","indian":"🍛","chinese":"🥡","american":"🍔","fast_food":"🌮","desserts":"🍰"}
    for r in restaurants:
        r.emoji = emoji_map.get(r.cuisine_type.value if r.cuisine_type else "", "🍴")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "restaurants": restaurants,
        "cuisines": cuisines
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
