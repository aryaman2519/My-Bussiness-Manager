# SmartStock 360 - Quick Setup Guide

## Step 1: Create Databases

```bash
cd backend
python scripts/create_tables.py
```

This creates two database files:
- `database.db` - Main business data (products, sales, inventory, etc.)
- `credentials.db` - User credentials (owners & staff)

## Step 2: Start Backend

```bash
cd backend
uvicorn app.main:app --reload
```

Backend runs on http://localhost:8000

## Step 3: Start Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
```

Frontend runs on http://localhost:5173

## Step 4: Register Owner Account

1. Go to http://localhost:5173/register
2. Fill the form:
   - Owner Full Name
   - Business Name
   - Username
   - Email (optional)
   - Password (minimum 6 characters)
3. Click "Register as Owner"
4. You'll be redirected to login page

## Step 5: Login

1. Use your username and password
2. You'll be taken to the dashboard

## Database Files

### Main Database (`database.db`)
- **Location**: `backend/database.db`
- **Contains**: Products, Sales, Inventory, Suppliers, etc.

### Credentials Database (`credentials.db`)
- **Location**: `backend/credentials.db`
- **Contains**: Owner registration credentials and staff auto-generated credentials
- **Security**: Separated from business data for better security

**View Credentials:**
```bash
cd backend
python scripts/view_credentials.py
```

## Troubleshooting

### "Module not found" errors
```bash
cd backend
pip install -r requirements.txt
```

### "Database not found"
```bash
cd backend
python scripts/create_tables.py
```

### Registration fails
- Check password is at least 6 characters
- Check username is unique
- Check backend server is running
- Check database.db file exists

