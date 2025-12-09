import os
import pkgutil
import importlib
from app.database.database import Base, engine
from app.models.users import *
from app.models.bank import *
from app.models.admin_role import *
from app.models.contact_us import *
from app.models.country import *
from app.models.exchange_rates import *
from app.models.kyc_documents import *
from app.models.manual_deposits import *
from app.models.notifications import *
from app.models.payment_cards import *
from app.models.recipients import *
from app.models.transactions import *
from app.models.transaction_fees import *
from app.models.boa_integration import *
def create_all_tables():
    print("🚀 Importing all model files...")
    
    print("🛠️ Creating tables in the database...")
    Base.metadata.create_all(bind=engine)

    print("✅ SUCCESS: All tables created!")



