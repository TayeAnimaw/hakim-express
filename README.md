# Hakim Express - Database Setup Guide

## 🎯 Database Configuration

Your application is now configured to work with **both SQLite (local development) and Supabase PostgreSQL (production)**.

### Current Setup:
- **Local Development**: Uses SQLite (`hakim_express.db`)
- **Production (Vercel)**: Uses Supabase PostgreSQL
- **Supabase API**: Always available for authentication, storage, etc.

## 🚀 Deployment Options

### Option 1: Vercel Deployment (Recommended)
1. **Database is ready** - All tables created in Supabase
2. **Set environment variables** in Vercel:
   ```
   DATABASE_URL=postgresql://postgres:FLfWeFXBXM0WPE3i@db.vexowistvjtaskacpsxj.supabase.co:5432/postgres?sslmode=require
   SUPABASE_URL=https://vexowistvjtaskacpsxj.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   # ... other env vars
   ```
3. **Deploy to Vercel** - Your app will automatically use Supabase

### Option 2: Local Development with Supabase
If you want to use Supabase locally too:
1. **Uncomment this line in `.env`**:
   ```
   DATABASE_URL=postgresql://postgres:FLfWeFXBXM0WPE3i@db.vexowistvjtaskacpsxj.supabase.co:5432/postgres?sslmode=require
   ```
2. **Run your app** - It will use Supabase PostgreSQL locally

### Option 3: Keep SQLite for Everything
- **Leave `.env` as-is** - Uses SQLite locally and on Vercel
- **Supabase API still works** for authentication and storage

## 📋 Database Tables Created

Your Supabase database now contains **17 tables**:
- `users` - User accounts
- `kyc_documents` - KYC verification
- `payment_cards` - Payment methods
- `transactions` - Money transfers
- `notifications` - User notifications
- `admin_roles`, `admin_permissions`, `admin_activities` - Admin system
- `banks`, `countries` - Reference data
- `exchange_rates`, `transaction_fees` - Financial data
- `recipients` - Transfer recipients
- `manual_deposits` - Deposit proofs
- `boa_transactions`, `boa_beneficiary_inquiries`, `boa_bank_list`, `boa_currency_rates`, `boa_balances` - BoA integration

## 🔧 Environment Variables

### Required for Production:
```bash
DATABASE_URL=postgresql://postgres:FLfWeFXBXM0WPE3i@db.vexowistvjtaskacpsxj.supabase.co:5432/postgres?sslmode=require
SUPABASE_URL=https://vexowistvjtaskacpsxj.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZleG93aXN0dmp0YXNrYWNwc3hqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTY4NjE2MCwiZXhwIjoyMDc3MjYyMTYwfQ.hXBXKrtoe9XNGjfZyolDqXDPv8f-nV8OFWJtnfIeeAk
SECRET_KEY=your-secret-key
MAIL_MAILER=smtp
MAIL_HOST=admin.heldertechnologies.com
MAIL_PORT=465
MAIL_USERNAME=support@admin.heldertechnologies.com
MAIL_PASSWORD=mariam21mariam21
MAIL_ENCRYPTION=ssl
MAIL_FROM_ADDRESS=support@admin.heldertechnologies.com
MAIL_FROM_NAME=AsccSystem Support
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## 🎉 Ready to Deploy!

Your application is fully configured for both local development and Vercel production deployment with Supabase. Choose your preferred setup and deploy!