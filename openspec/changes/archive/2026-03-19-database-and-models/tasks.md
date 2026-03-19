## 1. Database Setup

- [x] 1.1 Create `src/financial_pipeline/db.py` — async SQLite engine, session factory, and `create_tables` helper using SQLAlchemy async
- [x] 1.2 Create `src/financial_pipeline/models.py` — SQLAlchemy models for `accounts`, `imports`, and `transactions` per the design schema

## 2. App Integration

- [x] 2.1 Add lifespan handler to FastAPI app in `main.py` that creates tables on startup
- [x] 2.2 Add a temporary seed step that creates a few example internal accounts (placeholder until config module is designed)

## 3. Verification

- [x] 3.1 Run the app, verify `financial_pipeline.db` is created with correct tables and seed data
