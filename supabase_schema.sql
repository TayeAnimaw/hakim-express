-- Supabase Database Schema for Hakim Express
-- Run this SQL in your Supabase SQL Editor to create all tables

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop ALL existing objects in correct order (for complete reset)
-- First drop tables that reference other tables
DROP TABLE IF EXISTS boa_balances CASCADE;
DROP TABLE IF EXISTS boa_currency_rates CASCADE;
DROP TABLE IF EXISTS boa_bank_list CASCADE;
DROP TABLE IF EXISTS boa_beneficiary_inquiries CASCADE;
DROP TABLE IF EXISTS boa_transactions CASCADE;
DROP TABLE IF EXISTS manual_deposits CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS recipients CASCADE;
DROP TABLE IF EXISTS transaction_fees CASCADE;
DROP TABLE IF EXISTS exchange_rates CASCADE;
DROP TABLE IF EXISTS countries CASCADE;
DROP TABLE IF EXISTS contact_us CASCADE;
DROP TABLE IF EXISTS banks CASCADE;
DROP TABLE IF EXISTS admin_activities CASCADE;
DROP TABLE IF EXISTS admin_permissions CASCADE;
DROP TABLE IF EXISTS admin_roles CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS payment_cards CASCADE;
DROP TABLE IF EXISTS kyc_documents CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop existing types if they exist
DROP TYPE IF EXISTS user_role CASCADE;
DROP TYPE IF EXISTS kyc_status CASCADE;
DROP TYPE IF EXISTS transaction_status CASCADE;
DROP TYPE IF EXISTS account_type CASCADE;
DROP TYPE IF EXISTS card_type CASCADE;
DROP TYPE IF EXISTS gender_enum CASCADE;
DROP TYPE IF EXISTS id_type_enum CASCADE;
DROP TYPE IF EXISTS channel_type CASCADE;

-- Create custom types (enums)
CREATE TYPE user_role AS ENUM ('user', 'admin', 'finance_officer', 'support');
CREATE TYPE kyc_status AS ENUM ('pending', 'approved', 'rejected');
CREATE TYPE transaction_status AS ENUM ('pending', 'completed', 'failed', 'active');
CREATE TYPE account_type AS ENUM ('bank_account', 'telebirr');
CREATE TYPE card_type AS ENUM ('VISA', 'MASTER_CARD', 'AMERICAN_EXPRESS', 'DISCOVER', 'PAYONEER', 'OTHER');
CREATE TYPE gender_enum AS ENUM ('male', 'female', 'other');
CREATE TYPE id_type_enum AS ENUM ('passport', 'national_id', 'driver_license');
CREATE TYPE channel_type AS ENUM ('email', 'sms', 'push');

-- Users table
CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255),
    phone VARCHAR(255),
    password VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'user'::user_role,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    is_flagged BOOLEAN NOT NULL DEFAULT false,
    suspended_at TIMESTAMPTZ,
    suspension_reason TEXT,
    last_login TIMESTAMPTZ,
    two_factor_enabled BOOLEAN NOT NULL DEFAULT false,
    kyc_status kyc_status NOT NULL DEFAULT 'pending'::kyc_status,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    otp_code VARCHAR(6),
    otp_expires_at TIMESTAMPTZ,
    user_weekly_limit BIGINT,
    admin_notes TEXT,
    stripe_customer_id VARCHAR(255),
    profile_picture VARCHAR(255)
);

-- KYC Documents table
CREATE TABLE kyc_documents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    dob DATE NOT NULL,
    street_name VARCHAR(100),
    house_no VARCHAR(50),
    additional_info VARCHAR(255),
    postal_code VARCHAR(20),
    region VARCHAR(50),
    city VARCHAR(50),
    country VARCHAR(50),
    gender gender_enum,
    id_type id_type_enum DEFAULT 'national_id'::id_type_enum,
    front_image VARCHAR(255) NOT NULL,
    back_image VARCHAR(255),
    selfie_image VARCHAR(255) NOT NULL,
    status kyc_status DEFAULT 'pending'::kyc_status,
    rejection_reason TEXT,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Payment Cards table
CREATE TABLE payment_cards (
    payment_card_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    card_type card_type NOT NULL,
    stripe_payment_method_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    brand VARCHAR(50),
    last4 VARCHAR(4),
    exp_month INTEGER,
    exp_year INTEGER,
    is_default BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Transactions table
CREATE TABLE transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    payment_card_id BIGINT REFERENCES payment_cards(payment_card_id) ON DELETE CASCADE,
    stripe_charge_id VARCHAR(255),
    transaction_reference VARCHAR(255),
    amount DECIMAL(18,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'ETB',
    status transaction_status DEFAULT 'pending'::transaction_status,
    admin_note TEXT,
    is_manual BOOLEAN NOT NULL DEFAULT false,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    full_name VARCHAR(100) DEFAULT 'Taye',
    account_type account_type DEFAULT 'bank_account'::account_type,
    bank_name VARCHAR(100),
    account_number VARCHAR(50),
    telebirr_number VARCHAR(50),
    is_verified BOOLEAN NOT NULL DEFAULT false,
    transfer_fee DECIMAL(10,2) DEFAULT 3.2,
    manual_card_number VARCHAR(32),
    manual_card_exp_year VARCHAR(8),
    manual_card_cvc VARCHAR(8),
    manual_card_country VARCHAR(32),
    manual_card_zip VARCHAR(16)
);

-- All tables are already dropped at the beginning of the script

-- Admin Roles table
CREATE TABLE admin_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Admin Permissions table
CREATE TABLE admin_permissions (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL REFERENCES admin_roles(id) ON DELETE CASCADE,
    permission VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Admin Activities table
CREATE TABLE admin_activities (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL REFERENCES admin_roles(id) ON DELETE CASCADE,
    activity TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Banks table
CREATE TABLE banks (
    bank_id BIGSERIAL PRIMARY KEY,
    bank_name VARCHAR(100) NOT NULL UNIQUE,
    bank_code VARCHAR(20) NOT NULL UNIQUE
);

-- Contact Us table
CREATE TABLE contact_us (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Countries table
CREATE TABLE countries (
    country_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(10) NOT NULL UNIQUE
);

-- Exchange Rates table
CREATE TABLE exchange_rates (
    exchange_rate_id BIGSERIAL PRIMARY KEY,
    from_currency VARCHAR(10) NOT NULL,
    to_currency VARCHAR(10) NOT NULL,
    bank_name VARCHAR(255),
    buying_rate FLOAT,
    selling_rate FLOAT,
    rate DECIMAL(18,6),
    available_balance_from DECIMAL(18,2) DEFAULT 490.43,
    available_balance_to DECIMAL(18,2) DEFAULT 90.43,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Transaction Fees table
CREATE TABLE transaction_fees (
    id BIGSERIAL PRIMARY KEY,
    stripe_fee FLOAT DEFAULT 2.9,
    service_fee FLOAT DEFAULT 1.0,
    margin FLOAT DEFAULT 2.0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Recipients table
CREATE TABLE recipients (
    recipient_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    account_type account_type NOT NULL,
    bank_name VARCHAR(100),
    account_number VARCHAR(50),
    telebirr_number VARCHAR(50),
    amount VARCHAR(50) DEFAULT '0.0',
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Manual Deposits table
CREATE TABLE manual_deposits (
    id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    note TEXT,
    completed BOOLEAN NOT NULL DEFAULT false,
    deposit_proof_image VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- BoA Transactions table
CREATE TABLE boa_transactions (
    id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    boa_reference VARCHAR(100),
    unique_identifier VARCHAR(100),
    infinity_reference VARCHAR(100),
    transaction_type VARCHAR(50),
    boa_transaction_status VARCHAR(20) DEFAULT 'pending',
    debit_account_id VARCHAR(50),
    credit_account_id VARCHAR(50),
    debit_amount DECIMAL(18,2),
    credit_amount DECIMAL(18,2),
    debit_currency VARCHAR(10) DEFAULT 'ETB',
    credit_currency VARCHAR(10) DEFAULT 'ETB',
    reason VARCHAR(255),
    transaction_date VARCHAR(20),
    audit_info JSON,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- BoA Beneficiary Inquiries table
CREATE TABLE boa_beneficiary_inquiries (
    id BIGSERIAL PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    bank_id VARCHAR(20),
    customer_name VARCHAR(200),
    account_currency VARCHAR(10),
    enquiry_status VARCHAR(10),
    inquiry_type VARCHAR(20) NOT NULL,
    boa_response JSON,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- BoA Bank List table
CREATE TABLE boa_bank_list (
    id BIGSERIAL PRIMARY KEY,
    bank_id VARCHAR(20) NOT NULL UNIQUE,
    institution_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- BoA Currency Rates table
CREATE TABLE boa_currency_rates (
    id BIGSERIAL PRIMARY KEY,
    currency_code VARCHAR(10) NOT NULL,
    currency_name VARCHAR(50),
    buy_rate DECIMAL(18,4),
    sell_rate DECIMAL(18,4),
    boa_response JSON,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- BoA Balances table
CREATE TABLE boa_balances (
    id BIGSERIAL PRIMARY KEY,
    account_currency VARCHAR(10),
    balance DECIMAL(18,2),
    boa_response JSON,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Notifications table
CREATE TABLE notifications (
    notification_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    channel channel_type NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_sent BOOLEAN NOT NULL DEFAULT false,
    sent_at TIMESTAMPTZ,
    is_read BOOLEAN NOT NULL DEFAULT false,
    doc_metadata JSON,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_payment_cards_user_id ON payment_cards(user_id);
CREATE INDEX IF NOT EXISTS idx_kyc_documents_user_id ON kyc_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_boa_beneficiary_account ON boa_beneficiary_inquiries(account_id);

-- Add updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_kyc_documents_updated_at BEFORE UPDATE ON kyc_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payment_cards_updated_at BEFORE UPDATE ON payment_cards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_admin_roles_updated_at BEFORE UPDATE ON admin_roles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_exchange_rates_updated_at BEFORE UPDATE ON exchange_rates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_transaction_fees_updated_at BEFORE UPDATE ON transaction_fees FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_recipients_updated_at BEFORE UPDATE ON recipients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_manual_deposits_updated_at BEFORE UPDATE ON manual_deposits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_boa_transactions_updated_at BEFORE UPDATE ON boa_transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();