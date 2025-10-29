# Vercel Deployment Setup with Supabase

## Step 1: Create Tables in Supabase

1. Go to your Supabase Dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `supabase_schema.sql` and run it
4. This will create all necessary tables with proper relationships and constraints

## Step 2: Set Up Vercel Environment Variables

### How to Add Environment Variables in Vercel:

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Select your project** from the list
3. **Click on "Settings"** tab (gear icon)
4. **Click on "Environment Variables"** in the left sidebar
5. **Click "Add New"** button for each variable
6. **Fill in the details**:
   - **Name**: The variable name (e.g., `DATABASE_URL`)
   - **Value**: The variable value
   - **Environment**: Choose "Production" (or "Preview" if you want it for all deployments)
7. **Click "Save"** for each variable

### Required Environment Variables:

**Add each variable one by one using the "Add New" button:**

### Database Configuration
```
DATABASE_URL=postgresql://postgres:FLfWeFXBXM0WPE3i@db.vexowistvjtaskacpsxj.supabase.co:5432/postgres?sslmode=require
```
**Note**: This is the only variable you need to ADD to your current .env setup for Vercel

### Supabase Configuration (already working)
```
SUPABASE_URL=https://vexowistvjtaskacpsxj.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZleG93aXN0dmp0YXNrYWNwc3hqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTY4NjE2MCwiZXhwIjoyMDc3MjYyMTYwfQ.hXBXKrtoe9XNGjfZyolDqXDPv8f-nV8OFWJtnfIeeAk
```

### Other Required Variables
```
SECRET_KEY=4f66b8a5-97b1-44e0-91c1-1b5601293783
MAIL_MAILER=smtp
MAIL_HOST=admin.heldertechnologies.com
MAIL_PORT=465
MAIL_USERNAME=support@admin.heldertechnologies.com
MAIL_PASSWORD=mariam21mariam21
MAIL_ENCRYPTION=ssl
MAIL_FROM_ADDRESS=support@admin.heldertechnologies.com
MAIL_FROM_NAME=AsccSystem Support
STRIPE_SECRET_KEY=sk_test_51RLhHeBlr6AtFFQtyMKzly5bstaJ7IOGMSZM4V8spBkyf2AFEdi72EOXXirbE0IlkprBYcNNW46OlRSngEDI3gBV00onpYt3Gw
STRIPE_PUBLISHABLE_KEY=pk_test_51RLhHeBlr6AtFFQtG7TyMDYFu9PYeblqRdcT8KF6aaKYYo9fVNxuSYvbK06tSJgnosTZQrhTRmrvyDilI51wxheD00ickYaRtB
```

## Step 3: Deploy to Vercel

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Vercel will automatically detect it's a Python/FastAPI project
4. The deployment should work with the environment variables set above

## Step 4: Verify Deployment

After deployment, test that:
1. Your API endpoints work
2. Database connections are successful
3. Authentication works
4. All features function properly

## Important Notes

- **✅ Database Ready**: All 17 tables are already created in Supabase
- **✅ Local Development**: Your local setup uses SQLite for fast development
- **✅ Production**: Vercel will automatically use Supabase PostgreSQL
- **✅ Environment Variables**: All variables listed above must be set in Vercel
- **✅ Supabase API**: Already working for authentication and storage

## Quick Environment Variables Checklist

After adding all variables in Vercel, your list should include:
- ✅ DATABASE_URL
- ✅ SUPABASE_URL
- ✅ SUPABASE_KEY
- ✅ SECRET_KEY
- ✅ MAIL_MAILER, MAIL_HOST, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_ENCRYPTION, MAIL_FROM_ADDRESS, MAIL_FROM_NAME
- ✅ STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY

## Troubleshooting

If you encounter issues:
1. Check Vercel deployment logs
2. Verify all environment variables are set
3. Ensure the Supabase database schema is created
4. Test API endpoints after deployment

## Alternative Approach

If you prefer to use Supabase for both development and production:

1. Update your local `.env` file with the Supabase DATABASE_URL
2. Run the schema SQL in Supabase
3. Your application will work with PostgreSQL in both environments

This setup gives you the flexibility to use SQLite locally and PostgreSQL on Vercel.