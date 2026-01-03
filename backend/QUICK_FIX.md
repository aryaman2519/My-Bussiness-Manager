# Quick Fix for "no such table: user_credentials" Error

## The Problem
The `user_credentials` table doesn't exist in `credentials.db` yet.

## Solution 1: Restart Your Server (Easiest)
The server now automatically creates the table on startup. Just restart:

```bash
# Stop your current server (Ctrl+C)
# Then restart:
uvicorn app.main:app --reload
```

The table will be created automatically when the server starts.

## Solution 2: Create Table Manually
If you can't restart the server right now:

```bash
cd backend
python scripts/create_credentials_table.py
```

## Solution 3: Run Full Setup
Create both databases:

```bash
cd backend
python scripts/create_tables.py
```

## After Fixing
Once the table is created, try registering again. The registration should work now!

## Verify Table Exists
Check if the table was created:

```bash
cd backend
python scripts/view_credentials.py
```

If you see "No credentials found in database" (not an error), the table exists and is ready to use.



