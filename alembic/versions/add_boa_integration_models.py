"""add_boa_integration_models

Revision ID: add_boa_integration
Revises: e7a6be3225e1
Create Date: 2024-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_boa_integration'
down_revision = 'e7a6be3225e1'
previous_revision = 'e7a6be3225e1'
branch_labels = None
depends_on = None

def upgrade():
    # Create boa_transactions table
    op.create_table('boa_transactions',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('transaction_id', sa.BigInteger(), nullable=False),
        sa.Column('boa_reference', sa.String(length=100), nullable=True),
        sa.Column('unique_identifier', sa.String(length=100), nullable=True),
        sa.Column('infinity_reference', sa.String(length=100), nullable=True),
        sa.Column('transaction_type', sa.String(length=50), nullable=True),
        sa.Column('boa_transaction_status', sa.String(length=20), nullable=True),
        sa.Column('debit_account_id', sa.String(length=50), nullable=True),
        sa.Column('credit_account_id', sa.String(length=50), nullable=True),
        sa.Column('debit_amount', sa.DECIMAL(precision=18, scale=2), nullable=True),
        sa.Column('credit_amount', sa.DECIMAL(precision=18, scale=2), nullable=True),
        sa.Column('debit_currency', sa.String(length=10), nullable=True),
        sa.Column('credit_currency', sa.String(length=10), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('transaction_date', sa.String(length=20), nullable=True),
        sa.Column('audit_info', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.transaction_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_boa_transactions_id'), 'boa_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_boa_transactions_transaction_id'), 'boa_transactions', ['transaction_id'], unique=False)

    # Create boa_beneficiary_inquiries table
    op.create_table('boa_beneficiary_inquiries',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('account_id', sa.String(length=50), nullable=False),
        sa.Column('bank_id', sa.String(length=20), nullable=True),
        sa.Column('customer_name', sa.String(length=200), nullable=True),
        sa.Column('account_currency', sa.String(length=10), nullable=True),
        sa.Column('enquiry_status', sa.String(length=10), nullable=True),
        sa.Column('inquiry_type', sa.String(length=20), nullable=False),
        sa.Column('boa_response', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_boa_beneficiary_inquiries_id'), 'boa_beneficiary_inquiries', ['id'], unique=False)
    op.create_index(op.f('ix_boa_beneficiary_inquiries_account_id'), 'boa_beneficiary_inquiries', ['account_id'], unique=False)

    # Create boa_bank_list table
    op.create_table('boa_bank_list',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('bank_id', sa.String(length=20), nullable=False),
        sa.Column('institution_name', sa.String(length=200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_updated', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_boa_bank_list_id'), 'boa_bank_list', ['id'], unique=False)
    op.create_index(op.f('ix_boa_bank_list_bank_id'), 'boa_bank_list', ['bank_id'], unique=False)

    # Create boa_currency_rates table
    op.create_table('boa_currency_rates',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('currency_code', sa.String(length=10), nullable=False),
        sa.Column('currency_name', sa.String(length=50), nullable=True),
        sa.Column('buy_rate', sa.DECIMAL(precision=18, scale=4), nullable=True),
        sa.Column('sell_rate', sa.DECIMAL(precision=18, scale=4), nullable=True),
        sa.Column('boa_response', sa.JSON(), nullable=True),
        sa.Column('last_updated', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_boa_currency_rates_id'), 'boa_currency_rates', ['id'], unique=False)
    op.create_index(op.f('ix_boa_currency_rates_currency_code'), 'boa_currency_rates', ['currency_code'], unique=False)

    # Create boa_balances table
    op.create_table('boa_balances',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('account_currency', sa.String(length=10), nullable=True),
        sa.Column('balance', sa.DECIMAL(precision=18, scale=2), nullable=True),
        sa.Column('boa_response', sa.JSON(), nullable=True),
        sa.Column('last_updated', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_boa_balances_id'), 'boa_balances', ['id'], unique=False)

def downgrade():
    # Drop tables in reverse order
    op.drop_table('boa_balances')
    op.drop_table('boa_currency_rates')
    op.drop_table('boa_bank_list')
    op.drop_table('boa_beneficiary_inquiries')
    op.drop_table('boa_transactions')