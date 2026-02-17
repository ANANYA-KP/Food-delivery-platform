"""
Order management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import random
import string

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.models import (
    Order, OrderItem, MenuItem, Restaurant, Address, User,
    UserRole, OrderStatus, PaymentStatus, DeliveryPartner, AvailabilityStatus
)
from app.schemas.schemas import OrderCreate, OrderStatusUpdate, OrderResponse
from app.core.config import settings

router = APIRouter()

def generate_order_number() -> str:
    return "ORD-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


@router.post("/", response_model=OrderResponse, status_code=201)
async def place_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Place a new food order"""
    # Validate restaurant
    restaurant = db.query(Restaurant).filter(Restaurant.id == order_data.restaurant_id, Restaurant.is_active == True).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found or inactive")

    # Validate delivery address
    address = db.query(Address).filter(Address.id == order_data.delivery_address_id, Address.user_id == current_user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Delivery address not found")

    # Validate and price items
    subtotal = 0.0
    order_items_data = []
    for cart_item in order_data.items:
        menu_item = db.query(MenuItem).filter(
            MenuItem.id == cart_item.menu_item_id,
            MenuItem.restaurant_id == order_data.restaurant_id,
            MenuItem.is_available == True
        ).first()
        if not menu_item:
            raise HTTPException(status_code=404, detail=f"Menu item {cart_item.menu_item_id} not found")
        price = menu_item.discount_price if menu_item.discount_price else menu_item.price
        item_subtotal = price * cart_item.quantity
        subtotal += item_subtotal
        order_items_data.append({
            "menu_item_id": menu_item.id,
            "item_name": menu_item.name,
            "item_price": price,
            "quantity": cart_item.quantity,
            "subtotal": item_subtotal,
            "special_instructions": cart_item.special_instructions
        })

    # Check minimum order
    if subtotal < restaurant.min_order_amount:
        raise HTTPException(status_code=400, detail=f"Minimum order amount is ₹{restaurant.min_order_amount}")

    # Calculate charges
    tax_amount = round(subtotal * settings.TAX_PERCENTAGE / 100, 2)
    platform_fee = round(subtotal * settings.PLATFORM_FEE_PERCENTAGE / 100, 2)
    delivery_charge = restaurant.delivery_charge
    discount_amount = 0.0
    if order_data.promo_code == "FIRST50":
        discount_amount = min(50.0, subtotal * 0.1)
    total_amount = subtotal + tax_amount + delivery_charge + platform_fee - discount_amount

    estimated_delivery = datetime.utcnow() + timedelta(minutes=restaurant.avg_delivery_time + 10)

    # Create order
    order = Order(
        order_number=generate_order_number(),
        customer_id=current_user.id,
        restaurant_id=order_data.restaurant_id,
        delivery_address_id=order_data.delivery_address_id,
        subtotal=subtotal,
        tax_amount=tax_amount,
        delivery_charge=delivery_charge,
        platform_fee=platform_fee,
        discount_amount=discount_amount,
        total_amount=total_amount,
        payment_method=order_data.payment_method,
        payment_status=PaymentStatus.PENDING,
        promo_code=order_data.promo_code,
        special_instructions=order_data.special_instructions,
        estimated_delivery_time=estimated_delivery,
        status=OrderStatus.CONFIRMED,
        confirmed_at=datetime.utcnow()
    )
    db.add(order)
    db.flush()

    # Create order items
    for item_data in order_items_data:
        db.add(OrderItem(order_id=order.id, **item_data))

    # Auto-assign a delivery partner if available
    available_partner = db.query(DeliveryPartner).filter(
        DeliveryPartner.availability_status == AvailabilityStatus.ONLINE,
        DeliveryPartner.status == "approved"
    ).first()
    if available_partner:
        order.delivery_partner_id = available_partner.id
        available_partner.availability_status = AvailabilityStatus.BUSY

    db.commit()
    db.refresh(order)
    return order


@router.get("/", response_model=List[OrderResponse])
async def get_my_orders(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's orders"""
    if current_user.role == UserRole.CUSTOMER:
        query = db.query(Order).filter(Order.customer_id == current_user.id)
    elif current_user.role == UserRole.RESTAURANT:
        restaurant = db.query(Restaurant).filter(Restaurant.user_id == current_user.id).first()
        if not restaurant:
            return []
        query = db.query(Order).filter(Order.restaurant_id == restaurant.id)
    elif current_user.role == UserRole.DELIVERY_PARTNER:
        partner = db.query(DeliveryPartner).filter(DeliveryPartner.user_id == current_user.id).first()
        if not partner:
            return []
        query = db.query(Order).filter(Order.delivery_partner_id == partner.id)
    else:
        query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)

    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get order details with tracking status"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Permission check
    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update order status (restaurant/delivery partner/admin)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_status = status_update.status

    # Status transition rules
    allowed_transitions = {
        OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
        OrderStatus.PREPARING: [OrderStatus.READY_FOR_PICKUP],
        OrderStatus.READY_FOR_PICKUP: [OrderStatus.PICKED_UP],
        OrderStatus.PICKED_UP: [OrderStatus.OUT_FOR_DELIVERY],
        OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED],
    }
    allowed = allowed_transitions.get(order.status, [])
    if new_status not in allowed and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail=f"Cannot transition from {order.status} to {new_status}")

    order.status = new_status

    if new_status == OrderStatus.DELIVERED:
        order.actual_delivery_time = datetime.utcnow()
        order.payment_status = PaymentStatus.COMPLETED
        # Free up delivery partner
        if order.delivery_partner_id:
            partner = db.query(DeliveryPartner).filter(DeliveryPartner.id == order.delivery_partner_id).first()
            if partner:
                partner.availability_status = AvailabilityStatus.ONLINE
                partner.total_deliveries += 1
                partner.successful_deliveries += 1

    if new_status == OrderStatus.CANCELLED:
        order.cancelled_by = current_user.role.value
        if order.delivery_partner_id:
            partner = db.query(DeliveryPartner).filter(DeliveryPartner.id == order.delivery_partner_id).first()
            if partner:
                partner.availability_status = AvailabilityStatus.ONLINE

    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    reason: str = "Customer requested cancellation",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel an order"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel order in {order.status} state")

    order.status = OrderStatus.CANCELLED
    order.cancelled_by = current_user.role.value
    order.cancellation_reason = reason

    if order.delivery_partner_id:
        partner = db.query(DeliveryPartner).filter(DeliveryPartner.id == order.delivery_partner_id).first()
        if partner:
            partner.availability_status = AvailabilityStatus.ONLINE

    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}/track")
async def track_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Real-time order tracking information"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    tracking_steps = [
        {"step": "Order Confirmed", "status": OrderStatus.CONFIRMED, "icon": "✅"},
        {"step": "Preparing Food", "status": OrderStatus.PREPARING, "icon": "👨‍🍳"},
        {"step": "Ready for Pickup", "status": OrderStatus.READY_FOR_PICKUP, "icon": "📦"},
        {"step": "Picked Up", "status": OrderStatus.PICKED_UP, "icon": "🛵"},
        {"step": "Out for Delivery", "status": OrderStatus.OUT_FOR_DELIVERY, "icon": "🚀"},
        {"step": "Delivered", "status": OrderStatus.DELIVERED, "icon": "🎉"},
    ]
    status_order = [s["status"] for s in tracking_steps]
    current_index = status_order.index(order.status) if order.status in status_order else -1

    delivery_partner = None
    if order.delivery_partner_id:
        partner = db.query(DeliveryPartner).filter(DeliveryPartner.id == order.delivery_partner_id).first()
        if partner and partner.user:
            delivery_partner = {
                "name": partner.user.full_name,
                "phone": partner.user.phone,
                "vehicle_number": partner.vehicle_number,
                "rating": partner.rating,
                "latitude": partner.current_latitude,
                "longitude": partner.current_longitude,
            }

    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "current_status": order.status,
        "estimated_delivery_time": order.estimated_delivery_time,
        "actual_delivery_time": order.actual_delivery_time,
        "tracking_steps": [
            {**step, "completed": i <= current_index, "current": i == current_index}
            for i, step in enumerate(tracking_steps)
        ],
        "delivery_partner": delivery_partner,
        "restaurant": {
            "name": order.restaurant.name,
            "phone": order.restaurant.phone,
            "address": order.restaurant.address,
        }
    }
