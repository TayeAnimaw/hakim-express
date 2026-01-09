from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database.database import Base, SessionLocal, engine, init_redis
from app.seeders import create_admin_user
from app.routers import auth, users, payment_cards, recipients ,manual_deposits, notifications, kyc_documents, admin_kyc, admin_transactions,user_transactions, admin,dashboard, admin_exchange_rate, user_exchange_rate, admin_role, contact_us, admin_transaction_fees, admin_role,country, bank, user_transaction_fees, boa_integration
from app.seeders import create_admin_user
from app.core.security import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app = FastAPI(
    title="Hakim Express API",
    description="API documentation for Hakim Express.",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        create_admin_user(db)
    finally:
        db.close()
# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Adding CORS middleware for cross-origin requests (adjust as necessary)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
async def startup_event():
    """
    Function to run on application startup.
    Initializes Redis connection on startup.
    """
    await init_redis()
    print("Redis initialized successfully.")

app.include_router(dashboard.router, prefix="/api/admin", tags=["Dashboard"])
app.include_router(admin.router, prefix="/api", tags=["Admin User"])
app.include_router(admin_kyc.router, prefix="/api/admin/kyc", tags=["Admin - KYC Management"])
app.include_router(admin_transactions.router, prefix="/api/admin/transactions", tags=["Admin Transactions"])
app.include_router(admin_exchange_rate.router, prefix="/api/admin/exchange-rates", tags=["Admin currency & Fees management"])
app.include_router(admin_transaction_fees.router, prefix="/api/admin/transaction-fees", tags=["Admin - set Transaction Fees on fees and exchange rates page"])
app.include_router(user_transaction_fees.router, prefix="/api/user/transaction-fees", tags=["User - Transaction Fees"])
app.include_router(auth.router, prefix="/api/auth",tags=["Auth"])
app.include_router(users.router, prefix="/api", tags=["Profile Management"])
app.include_router(kyc_documents.router, prefix="/api/kyc", tags=["User - KYC Documents"])
app.include_router(payment_cards.router, prefix="/api/payment-cards", tags=[" User Payment Cards"])
app.include_router(user_transactions.router, prefix="/api/user/transactions", tags=["User Transactions"])
app.include_router(user_exchange_rate.router, prefix="/api/user/exchange-rates", tags=["User Exchange Rates"])
app.include_router(manual_deposits.router, prefix="/api/manual-deposits", tags=["Manual Deposits"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(contact_us.router, prefix="/api/contacts", tags=["Contact Us"])
app. include_router(admin_role.router, prefix="/api/admin/roles", tags=["Admin Roles and Permissions"])
app.include_router(country.router, prefix="/api/countries", tags=["Countries List"])
app.include_router(bank.router, prefix="/api/banks", tags=["Banks List"])
app.include_router(boa_integration.router, prefix="/api/boa", tags=["Bank of Abyssinia Integration"])



# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to Hakim Express APi Endpoints Documentation"}
