from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.security import create_stripe_payment_method
from app.database.database import get_db
from app.models.payment_cards import PaymentCard
from app.schemas.payment_cards import PaymentCardCreate, PaymentCardUpdate, PaymentCardResponse
from app.models.users import User
from app.security import JWTBearer, get_current_user  # Use your actual token-based auth dependency
import stripe
from app.core.config import settings  # Add this if you're using .env
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

@router.post("/", response_model=PaymentCardResponse)
def create_payment_card(
    payment_card: PaymentCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Step 1: Create Stripe customer if needed

        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(email=current_user.email)
            current_user.stripe_customer_id = customer.id
            db.commit()
        else:
            customer = stripe.Customer.retrieve(current_user.stripe_customer_id)


        # Step 2: Attach payment method to customer
        # if you get demo payment method from the above create_stripe_payment_method function and pass 
        # the stripe payment_method_id in the request body you must comment the below try except block
        # commented block is for test token only we must use the below code in production
        try:
            
            stripe.PaymentMethod.attach(
                payment_card.stripe_payment_method_id,
                customer=customer.id,
            )
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {e.user_message}")

        # Step 3: Set as default if specified
        if payment_card.is_default:
            stripe.Customer.modify(
                customer.id,
                invoice_settings={"default_payment_method": payment_card.stripe_payment_method_id},
            )
            db.query(PaymentCard).filter(
                PaymentCard.user_id == current_user.user_id,
                PaymentCard.is_default == True
            ).update({"is_default": False})
            db.commit()

        # Step 4: Retrieve card metadata from Stripe
        method = stripe.PaymentMethod.retrieve(payment_card.stripe_payment_method_id)
        card_info = method.card

        new_card = PaymentCard(
            user_id=current_user.user_id,
            stripe_customer_id=customer.id,
            stripe_payment_method_id=payment_card.stripe_payment_method_id,
            brand=card_info.brand,
            last4=card_info.last4,
            exp_month=card_info.exp_month,
            exp_year=card_info.exp_year,
            is_default=payment_card.is_default,
            is_active=True,
            card_type=payment_card.card_type,
        )

        db.add(new_card)
        db.commit()
        db.refresh(new_card)
        
        return new_card
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal_server_error")
@router.get("/", response_model=List[PaymentCardResponse])
def get_my_payment_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cards = db.query(PaymentCard).filter(
        PaymentCard.user_id == current_user.user_id,
        PaymentCard.is_active == True
    ).all()

    return cards


@router.get("/default", response_model=PaymentCardResponse)
def get_default_payment_card(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    card = db.query(PaymentCard).filter(
        PaymentCard.user_id == current_user.user_id,
        PaymentCard.is_default == True,
        PaymentCard.is_active == True
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="No default card found")
    return card


@router.put("/{payment_card_id}", response_model=PaymentCardResponse)
def update_payment_card(
    payment_card_id: int,
    update_data: PaymentCardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    card = db.query(PaymentCard).filter_by(payment_card_id=payment_card_id).first()

    if not card or card.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized or card not found")

    if update_data.is_default:
        db.query(PaymentCard).filter(
            PaymentCard.user_id == current_user.user_id,
            PaymentCard.is_default == True,
            PaymentCard.payment_card_id != payment_card_id
        ).update({"is_default": False})
        db.commit()

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(card, key, value)

    db.commit()
    db.refresh(card)
    return card


@router.put("/{payment_card_id}/set_default")
def set_default_card(
    payment_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    card = db.query(PaymentCard).filter_by(payment_card_id=payment_card_id).first()

    if not card or card.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized or card not found")
    # first we must make false to existing default card because only one card can be default
    # then we can set this card as default
    default_card = db.query(PaymentCard).filter_by(
        user_id=current_user.user_id,
        is_default=True
    ).first()
    if default_card:
        default_card.is_default = False
        db.commit()
        db.refresh(default_card)
      # Unset existing default
    db.query(PaymentCard).filter(
        PaymentCard.user_id == current_user.user_id,
        PaymentCard.is_default == True
    ).update({"is_default": False})
     # Set this card as default
    card.is_default = True
    db.commit()
    db.refresh(card)
    return {"detail": "Default card updated successfully"}


@router.delete("/{payment_card_id}")
def delete_payment_card(
    payment_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    card = db.query(PaymentCard).filter_by(payment_card_id=payment_card_id).first()

    if not card or card.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized or card not found")

    card.is_active = False
    db.commit()
    return {"detail": "Payment card deactivated successfully"}

@router.post("/")
async def pay_with_card(
    amount: float,
    token: dict = Depends(JWTBearer()),
    db: Session = Depends(get_db) 
):
    current_user = get_current_user(db, token)
    if(current_user is None):
        raise HTTPException(status_code=401, detail="Unauthorized")
    from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.security import create_stripe_payment_method
from app.database.database import get_db
from app.models.payment_cards import PaymentCard
from app.schemas.payment_cards import PaymentCardCreate, PaymentCardUpdate, PaymentCardResponse
from app.models.users import User
from app.security import JWTBearer, get_current_user  # Use your actual token-based auth dependency
import stripe
from app.core.config import settings  # Add this if you're using .env
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

@router.post("/", response_model=PaymentCardResponse)
def create_payment_card(
    payment_card: PaymentCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Step 1: Create Stripe customer if needed

        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(email=current_user.email)
            current_user.stripe_customer_id = customer.id
            db.commit()
        else:
            customer = stripe.Customer.retrieve(current_user.stripe_customer_id)


        # Step 2: Attach payment method to customer
        # if you get demo payment method from the above create_stripe_payment_method function and pass 
        # the stripe payment_method_id in the request body you must comment the below try except block
        # commented block is for test token only we must use the below code in production
        try:
            
            stripe.PaymentMethod.attach(
                payment_card.stripe_payment_method_id,
                customer=customer.id,
            )
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {e.user_message}")

        # Step 3: Set as default if specified
        if payment_card.is_default:
            stripe.Customer.modify(
                customer.id,
                invoice_settings={"default_payment_method": payment_card.stripe_payment_method_id},
            )
            db.query(PaymentCard).filter(
                PaymentCard.user_id == current_user.user_id,
                PaymentCard.is_default == True
            ).update({"is_default": False})
            db.commit()

        # Step 4: Retrieve card metadata from Stripe
        method = stripe.PaymentMethod.retrieve(payment_card.stripe_payment_method_id)
        card_info = method.card

        new_card = PaymentCard(
            user_id=current_user.user_id,
            stripe_customer_id=customer.id,
            stripe_payment_method_id=payment_card.stripe_payment_method_id,
            brand=card_info.brand,
            last4=card_info.last4,
            exp_month=card_info.exp_month,
            exp_year=card_info.exp_year,
            is_default=payment_card.is_default,
            is_active=True,
            card_type=payment_card.card_type,
        )

        db.add(new_card)
        db.commit()
        db.refresh(new_card)
        
        return new_card
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal_server_error")
@router.get("/", response_model=List[PaymentCardResponse])
def get_my_payment_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cards = db.query(PaymentCard).filter(
        PaymentCard.user_id == current_user.user_id,
        PaymentCard.is_active == True
    ).all()

    return cards


@router.get("/default", response_model=PaymentCardResponse)
def get_default_payment_card(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    card = db.query(PaymentCard).filter(
        PaymentCard.user_id == current_user.user_id,
        PaymentCard.is_default == True,
        PaymentCard.is_active == True
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="No default card found")
    return card


@router.put("/{payment_card_id}", response_model=PaymentCardResponse)
def update_payment_card(
    payment_card_id: int,
    update_data: PaymentCardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    card = db.query(PaymentCard).filter_by(payment_card_id=payment_card_id).first()

    if not card or card.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized or card not found")

    if update_data.is_default:
        db.query(PaymentCard).filter(
            PaymentCard.user_id == current_user.user_id,
            PaymentCard.is_default == True,
            PaymentCard.payment_card_id != payment_card_id
        ).update({"is_default": False})
        db.commit()

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(card, key, value)

    db.commit()
    db.refresh(card)
    return card
@router.put("/{payment_card_id}/set_default")
def set_default_card(
    payment_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    card = db.query(PaymentCard).filter_by(payment_card_id=payment_card_id).first()
    if not card or card.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized or card not found")
    default_card = db.query(PaymentCard).filter_by(
        user_id=current_user.user_id,
        is_default=True
    ).first()
    if default_card:
        default_card.is_default = False
        db.commit()
        db.refresh(default_card)
      # Unset existing default
    db.query(PaymentCard).filter(
        PaymentCard.user_id == current_user.user_id,
        PaymentCard.is_default == True
    ).update({"is_default": False})
     # Set this card as default
    card.is_default = True
    db.commit()
    db.refresh(card)
    return {"detail": "Default card updated successfully"}


@router.delete("/{payment_card_id}")
def delete_payment_card(
    payment_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    card = db.query(PaymentCard).filter_by(payment_card_id=payment_card_id).first()

    if not card or card.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized or card not found")

    card.is_active = False
    db.commit()
    return {"detail": "Payment card deactivated successfully"}

@router.post("/pay")
async def pay_with_card(
    amount: float,
    token: dict = Depends(JWTBearer()),
    db: Session = Depends(get_db) 
):
    current_user = get_current_user(db, token)
    if(current_user is None):
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # find user stipe payment id
        stripe_customer_id = current_user.stripe_customer_id
        if not stripe_customer_id:
            raise HTTPException(status_code=400, detail="Customer ID not found")
        card = db.query(PaymentCard).filter(
            PaymentCard.user_id == current_user.user_id,
            PaymentCard.is_default == True,
            PaymentCard.is_active == True
        ).first()
        if not card:
            raise HTTPException(status_code=400, detail="No default payment card found")
        intent = stripe.PaymentIntent.create(
            amount=int(amount),
            currency="usd",
            customer=stripe_customer_id,
            payment_method=card.stripe_payment_method_id,
            confirm=True,
            automatic_payment_methods={
                "enabled": True,
                "allow_redirects": "never"
            }
        )

        return {
            "message": "Payment successful",
            "payment_intent": intent
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=e.user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Payment failed")
        