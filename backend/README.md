# SmartStock 360 Backend

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Databases

```bash
python scripts/create_tables.py
```

This creates:
- `database.db` - Main business data
- `credentials.db` - User credentials (owners & staff)

### 3. Start Server

```bash
uvicorn app.main:app --reload
```

Server runs on http://localhost:8000

## Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=sqlite:///./database.db
SECRET_KEY=your-secret-key-minimum-32-characters-long
```

## Databases

SmartStock 360 uses **two separate SQLite databases**:

### 1. Main Database (`database.db`)
- **Location**: `backend/database.db`
- **Stores**: Products, Sales, Inventory, Suppliers, Purchase Orders, etc.
- **Purpose**: All business data

### 2. Credentials Database (`credentials.db`)
- **Location**: `backend/credentials.db`
- **Stores**: User credentials (owners & staff)
- **Purpose**: Secure storage of authentication data
- **Tables**: `user_credentials`

**Note**: Credentials are stored separately for security. Both databases are created automatically.

## API Endpoints

- `POST /api/auth/register` - Register owner account
- `POST /api/auth/token` - Login
- `POST /api/staff/create` - Create staff (owner only)
- `GET /api/staff/list` - List staff (owner only)

## View Database

```bash
python scripts/view_database.py
```

