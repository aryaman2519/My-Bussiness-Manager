# Viewing Passwords in Credentials Database

## How It Works

The credentials database now stores passwords in two ways:

1. **Hashed Password** (always stored)
   - Used for authentication
   - Secure bcrypt hash
   - Stored for both owners and staff

2. **Plain Password** (only for staff)
   - Only stored for auto-generated staff passwords
   - Allows owners to view and share passwords with staff
   - NOT stored for owner accounts (security)

## View All Credentials

```bash
cd backend
python scripts/view_credentials.py
```

This will show:
- **Staff accounts**: Plain password + hashed password
- **Owner accounts**: Only hashed password (plain password not stored for security)

## Example Output

```
👤 John Doe (john_123)
   Role: STAFF
   Email: N/A
   Business: My Mobile Store
   Password Type: 🔑 Auto-generated
   🔓 Plain Password: Abc123Xy
   🔐 Hashed Password: $2b$12$abcdefghijklmnopqrstuvwxyz...
   Status: ✅ Active
   Created: 2024-01-15 10:30:00

👑 Owner Name (owner1)
   Role: OWNER
   Email: owner@example.com
   Business: My Mobile Store
   Password Type: ✏️ User-set
   🔒 Password: [Hashed - Owner set their own password]
   🔐 Hashed Password: $2b$12$xyzabcdefghijklmnopqrstuv...
   Status: ✅ Active
   Created: 2024-01-15 09:00:00
```

## Security Notes

- **Owner passwords**: Never stored in plain text (you set your own password)
- **Staff passwords**: Stored in plain text because they're auto-generated and need to be shared
- **Hashed passwords**: Always used for actual authentication
- **Best practice**: Change staff passwords after first login (if you implement that feature)

## Update Existing Database

If you have an existing `credentials.db` file, run:

```bash
cd backend
python scripts/migrate_add_plain_password.py
```

This adds the `plain_password` column to your existing database.

## For New Staff Accounts

When you create a new staff account:
1. The system generates a password
2. Stores it in **both** plain and hashed form
3. Shows you the plain password (save it!)
4. The plain password is stored in `credentials.db` so you can view it later



