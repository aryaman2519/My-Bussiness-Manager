# SmartStock 360 – Retail Management & Market Intelligence

SmartStock 360 unifies inventory intelligence, digital billing, warranty tracking, and market-aware pricing for mobile retail stores.

## Repository Layout

- `backend/` – FastAPI service (inventory, alerts, billing APIs).
- `frontend/` – Vite + React dashboard for command-center experience.
- `docs/` (future) – Specifications, API contracts, ML notebooks.

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt

# Create database tables (first time only)
python scripts/create_tables.py

# Start the server
uvicorn app.main:app --reload
```

**Note**: Create `backend/.env` file with:
```env
DATABASE_URL=sqlite:///./database.db
SECRET_KEY=your-secret-key-minimum-32-characters-long
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Vite serves the dashboard on http://localhost:5173.

**Note**: If you see "Failed to resolve import 'react-router-dom'" error, run:
```bash
npm install react-router-dom
```

## Features

### 🔐 Role-Based Authentication System
- **Owner (Super Admin)**: Full access to profit margins, landing costs, supplier details. Can create staff accounts, manage inventory, and change prices.
- **Staff (Salesperson)**: Limited access - can only see selling prices and stock quantities. Can create bills and search items. Cannot see profit margins or delete stock history.
- No sign-up button - Owner account created via database script
- JWT-based authentication with secure password hashing
- Protected routes and role-based UI components

### 🏠 Interactive Homepage
- Modern, responsive landing page showcasing all SmartStock 360 features
- Hero section with animated background elements
- Feature cards for all 5 core modules:
  - 📊 Inventory & Low-Stock Watchtower (Velocity-Based Alerts)
  - 🧾 Digital Billing & Warranty Vault (IMEI Tracking)
  - 💹 Market Pulse Price Comparator (Profit Margin Calculator)
  - 🤖 Dynamic Restock Prediction (ML Forecasting)
  - 📱 Smart Search & Barcode Integration
- Interactive hover effects and smooth animations
- Stats section and call-to-action areas

### Phase 1 Scope

1. Inventory CRUD with barcode/IMEI metadata.
2. Velocity-based low-stock alert service + notification hooks (Twilio/WhatsApp).
3. Digital billing UI skeleton (invoice creation, IMEI capture placeholders).
4. Market Pulse cards ready to connect to scraping microservices.

## Database Setup

SmartStock 360 uses **SQLite** (built-in database, no server needed).

**Quick Start:**
```bash
# 1. Create database tables (creates database.db file)
cd backend
python scripts/create_tables.py

# 2. Start backend server
uvicorn app.main:app --reload

# 3. Start frontend (in another terminal)
cd frontend
npm run dev

# 4. Register owner account at http://localhost:5173/register
```

**View Your Database Data:**
```bash
cd backend
python scripts/view_database.py
```

**Database Files:**
- **Main Database** (`database.db`): Products, Sales, Inventory, etc.
- **Credentials Database** (`credentials.db`): Owner & Staff credentials (separated for security)

**View Credentials:**
```bash
cd backend
python scripts/view_credentials.py
```

### Database Schema

The system includes comprehensive models for:
- **Users** (Owner/Staff with role-based access)
- **Products** (Catalog with pricing - landing cost hidden from staff)
- **Inventory** (Stock levels, velocity tracking, reorder alerts)
- **Sales** (Transactions, invoices, profit tracking)
- **Warranties** (IMEI tracking, warranty claims)
- **Suppliers** (Vendor management)
- **Purchase Orders** (Stock procurement)
- **Stock Movements** (Complete inventory history)
- **Price History** (Price change tracking)

## Next Steps

- Connect React Query hooks to the FastAPI endpoints for live data.
- Implement inventory CRUD operations with role-based access.
- Build billing interface with IMEI capture.
- Add market pulse price scraping integration.
- Introduce automated tests (Pytest, Vitest).

Contributions and iterations are welcome—open issues or reach out if you want to tackle a specific feature.

