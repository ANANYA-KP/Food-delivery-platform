# 🍕 Online Food Delivery Platform

A complete Python + FastAPI backend project built from the Application Requirements document.  
Runs **100% locally in VSCode** with **no external services needed** (uses SQLite).

---

## 📋 What This Project Includes

Based on the full requirements spec, this project implements:

| Module | Features Implemented |
|--------|---------------------|
| 🔐 Authentication | Register (email/phone), Login, OTP verification, JWT tokens, Refresh token, Password reset |
| 👤 Customer Module | Profile management, Multiple addresses, Browse restaurants, Filters (cuisine/veg/rating/city), Sorting |
| 🍽️ Restaurant Module | Register restaurant, Menu CRUD (add/edit/delete), Order notifications, Accept/reject orders |
| 📦 Order & Cart | Place orders, Calculate totals with tax & delivery charge, Promo codes, Real-time status tracking |
| 🛵 Delivery Partners | Register, Proximity-based auto-assignment, GPS location update, Status updates (Picked Up → Delivered) |
| ⭐ Ratings & Reviews | Rate restaurants + delivery partners, Review text, Auto-update average ratings |
| 🔧 Admin Dashboard | User management (block/unblock), Restaurant approvals, Order monitoring, Revenue reports |

**Payment Methods Supported:** UPI, Credit/Debit Card, Net Banking, Cash on Delivery  
**Order Tracking States:** Confirmed → Preparing → Ready → Picked Up → Out for Delivery → Delivered

---

## 🚀 Quick Setup (VSCode)

### Step 1 — Open project in VSCode

```
File → Open Folder → select the `food_delivery` folder
```

### Step 2 — Create Virtual Environment

Open VSCode Terminal (`Ctrl + \``) and run:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `sqlalchemy` — Database ORM
- `python-jose` — JWT authentication
- `passlib[bcrypt]` — Password hashing
- `pydantic` — Data validation
- `jinja2` — HTML templates

### Step 4 — Run the Server

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5 — Open in Browser

| URL | What you'll see |
|-----|----------------|
| http://localhost:8000 | 🏠 Homepage with all info |
| http://localhost:8000/docs | 📖 Interactive Swagger UI (test all APIs) |

---

## 🔑 Demo Login Credentials

These are auto-created when you first run the server.

| Role | Email | Password |
|------|-------|----------|
| 🔧 Admin | admin@fooddelivery.com | admin123 |
| 👤 Customer | customer@example.com | customer123 |
| 🍽️ Restaurant Owner | owner@pizzapalace.com | owner123 |
| 🛵 Delivery Partner | rider@example.com | rider123 |

---

## 🧪 How to Test APIs in Swagger UI

1. Go to **http://localhost:8000/docs**
2. Click **POST /api/v1/auth/login**
3. Click **Try it out**
4. Enter:
   ```json
   {
     "email_or_phone": "customer@example.com",
     "password": "customer123"
   }
   ```
5. Copy the `access_token` from the response
6. Click the **🔒 Authorize** button (top right)
7. Enter: `Bearer <your_token_here>`
8. Now all protected APIs are unlocked!

---

## 📁 Project Structure

```
food_delivery/
│
├── main.py                          ← 🚀 Entry point — run this file
├── requirements.txt                 ← 📦 All dependencies
├── .env                             ← ⚙️ Configuration
├── food_delivery.db                 ← 🗄️ SQLite database (auto-created)
│
├── app/
│   ├── core/
│   │   ├── config.py               ← App settings
│   │   ├── database.py             ← SQLAlchemy setup (SQLite)
│   │   └── security.py             ← JWT + password hashing
│   │
│   ├── models/
│   │   └── models.py               ← All database models:
│   │                                  User, Address, Restaurant, MenuItem
│   │                                  Order, OrderItem, DeliveryPartner, Rating
│   │
│   ├── schemas/
│   │   └── schemas.py              ← Pydantic request/response schemas
│   │
│   └── api/
│       ├── deps.py                 ← Auth dependencies
│       └── v1/
│           ├── api.py              ← Combines all routers
│           └── endpoints/
│               ├── auth.py         ← Register, Login, OTP, Refresh
│               ├── restaurants.py  ← Restaurant + Menu CRUD
│               ├── orders.py       ← Place, Track, Cancel orders
│               ├── users.py        ← Profile, Addresses, Ratings, Delivery
│               └── admin.py        ← Admin dashboard & reports
│
├── static/                         ← CSS/JS files
├── templates/                      ← HTML templates
├── uploads/                        ← File uploads
└── logs/                           ← Application logs
```

---

## 📡 Key API Endpoints

### Authentication
```
POST /api/v1/auth/register       → Register new user
POST /api/v1/auth/login          → Login (get JWT token)
POST /api/v1/auth/request-otp   → Request phone OTP
POST /api/v1/auth/verify-otp    → Verify OTP
POST /api/v1/auth/refresh        → Refresh access token
GET  /api/v1/auth/me             → Get current user
```

### Restaurants
```
GET    /api/v1/restaurants/                     → Browse restaurants (with filters)
GET    /api/v1/restaurants/{id}                 → Restaurant details
POST   /api/v1/restaurants/                     → Create restaurant
GET    /api/v1/restaurants/{id}/menu            → Get menu items
POST   /api/v1/restaurants/{id}/menu            → Add menu item
PUT    /api/v1/restaurants/{id}/menu/{item_id}  → Update menu item
DELETE /api/v1/restaurants/{id}/menu/{item_id}  → Delete menu item
```

### Orders
```
POST   /api/v1/orders/                → Place a new order
GET    /api/v1/orders/                → My orders list
GET    /api/v1/orders/{id}            → Order details
GET    /api/v1/orders/{id}/track      → Real-time tracking info
PATCH  /api/v1/orders/{id}/status     → Update order status
POST   /api/v1/orders/{id}/cancel     → Cancel order
```

### Users
```
GET  /api/v1/users/profile           → Get profile
PUT  /api/v1/users/profile           → Update profile
GET  /api/v1/users/addresses         → List addresses
POST /api/v1/users/addresses         → Add address
DEL  /api/v1/users/addresses/{id}    → Delete address
```

### Admin
```
GET    /api/v1/admin/dashboard                → Stats overview
GET    /api/v1/admin/users                    → All users
PATCH  /api/v1/admin/users/{id}/block         → Block user
PATCH  /api/v1/admin/restaurants/{id}/approve → Approve restaurant
GET    /api/v1/admin/reports/revenue          → Revenue reports (daily/monthly)
GET    /api/v1/admin/reports/restaurants      → Restaurant performance
```

---

## 🧪 Sample Test Flow

```bash
# 1. Register a new customer
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email_or_phone":"test@example.com","password":"test123"}'

# 3. Browse restaurants (no auth needed)
curl http://localhost:8000/api/v1/restaurants/

# 4. Get menu of restaurant 1
curl http://localhost:8000/api/v1/restaurants/1/menu
```

---

## ⚙️ Configuration (.env)

```env
APP_NAME=Food Delivery Platform
DEBUG=True
DATABASE_URL=sqlite:///./food_delivery.db    # Uses SQLite locally
SECRET_KEY=your-secret-key-here
TAX_PERCENTAGE=5.0
PLATFORM_FEE_PERCENTAGE=2.0
```

For production, change `DATABASE_URL` to PostgreSQL:
```
DATABASE_URL=postgresql://user:password@localhost:5432/food_delivery_db
```

---

## 🔄 Reset Demo Data

Delete the database file and restart:
```bash
rm food_delivery.db
python main.py
```

---

## 📦 Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python 3.10+ | Language |
| FastAPI | REST API framework |
| SQLAlchemy | ORM (database access) |
| SQLite | Database (local dev) |
| Pydantic v2 | Data validation |
| python-jose | JWT token auth |
| passlib/bcrypt | Password hashing |
| Uvicorn | ASGI server |

---

## 🔮 Future Enhancements (from requirements)
- AI-based food recommendations
- Subscription plans
- Scheduled deliveries
- In-app wallet
- Live chat support
- WebSocket for real-time tracking
- Razorpay/Stripe payment integration
- Twilio SMS for OTP
- Google Maps API for distance calculation
