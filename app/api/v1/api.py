"""
Main API Router - combines all endpoint routers
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, restaurants, orders, admin
from app.api.v1.endpoints.users import users_router, delivery_router, ratings_router

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["🔐 Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["👤 Users & Addresses"])
api_router.include_router(restaurants.router, prefix="/restaurants", tags=["🍽️ Restaurants & Menu"])
api_router.include_router(orders.router, prefix="/orders", tags=["📦 Orders & Tracking"])
api_router.include_router(delivery_router, prefix="/delivery", tags=["🛵 Delivery Partners"])
api_router.include_router(ratings_router, prefix="/ratings", tags=["⭐ Ratings & Reviews"])
api_router.include_router(admin.router, prefix="/admin", tags=["🔧 Admin Panel"])
