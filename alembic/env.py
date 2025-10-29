# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from app.database.database import Base  # Import your Base
from app.models.exchange_rates import ExchangeRate  # Import your models
from app.models.users import User  # Import your models
from app.models.payment_cards import PaymentCard  # Import your models
from app.models.recipients import Recipient  # Import your models
from app.models.transactions import Transaction  # Import your models
from app.models.manual_deposits import ManualDeposit  # Import your models
from app.models.notifications import Notification  # Import your models
from app.models.kyc_documents import KYCDocument  # Import your models
from app.models.transaction_fees import TransactionFees  # Import your models
from app.models.admin_role import AdminRole, AdminPermission, AdminActivity  # Import your models
from app.models.contact_us import ContactUs  # Import your models
from app.models.country import Country  # Import your models
from app.models.bank import Bank  # Import your models




from alembic import context

# Set target_metadata to your Base's metadata
target_metadata = Base.metadata

# Alembic Config object for accessing .ini file values
config = context.config

# Setting up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()