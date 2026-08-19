# Kenya Secondary School ERP - Backend Setup Guide

## PHASE 1: Core Scaffolding & Authentication - COMPLETE ✅

This guide walks through setting up the backend locally.

## Prerequisites

- Python 3.11+
- PostgreSQL 16+ (or Docker)
- Redis 5.0+ (or Docker)
- pip or Poetry

## Quick Start

### 1. Clone & Setup Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and populate with your local values:

```bash
cp .env.example .env
```

**Key values to set:**
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `ENCRYPTION_KEY`: Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Your PostgreSQL credentials
- `REDIS_HOST`, `REDIS_PORT`: Your Redis credentials

### 3. Initialize Database

```bash
# Create Alembic migrations directory (one-time)
alembic init -t async alembic

# Run migrations (creates tables)
alembic upgrade head

# OR let FastAPI auto-create tables on startup (development only)
python -m uvicorn src.main:app --reload
```

### 4. Run Development Server

```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Server runs at http://localhost:8000
API docs at http://localhost:8000/api/v1/docs

## Project Structure

```
backend/
├── src/
│   ├── core/                 # Core services (config, database, security)
│   │   ├── __init__.py
│   │   ├── config.py         # Pydantic settings from .env
│   │   ├── database.py       # AsyncSession & engine
│   │   └── security.py       # JWT, password hashing
│   ├── shared/               # Shared patterns (base models, exceptions)
│   │   ├── base_model.py     # SQLAlchemy Base + AuditableBase
│   │   ├── base_repository.py # Generic CRUD
│   │   ├── exceptions.py     # Custom HTTP exceptions
│   │   ├── response.py       # APIResponse wrapper
│   │   └── pagination.py     # Pagination schemas
│   ├── modules/              # Domain-driven contexts
│   │   ├── users/            # User management (PHASE 1)
│   │   │   ├── models.py     # User, Role, Permission SQLAlchemy models
│   │   │   ├── schemas.py    # Pydantic request/response schemas
│   │   │   ├── repository.py # Database access layer
│   │   │   ├── services.py   # Business logic
│   │   │   └── routers.py    # API endpoints
│   │   ├── finance/          # Finance module (PHASE 2)
│   │   ├── academics/        # Academic module (PHASE 3)
│   │   └── ...
│   └── main.py               # FastAPI app initialization
├── pyproject.toml            # Poetry dependency manifest
├── requirements.txt          # pip requirements (auto-generated from pyproject.toml)
├── .env.example              # Environment template
└── alembic/                  # Database migrations
    ├── versions/             # Individual migration files
    └── env.py
```

## Testing API Endpoints

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@school.edu",
    "password": "SecurePassword123!"
  }'
```

Returns:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGci...",
    "token_type": "bearer"
  }
}
```

### 3. Get Current User

Use the access token from login:

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Refresh Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
  -b "refresh_token=YOUR_REFRESH_TOKEN; csrf_token=YOUR_CSRF_TOKEN"
```

## Authentication Architecture

- **Access Token**: Short-lived (30 min), stored in memory/local storage
- **Refresh Token**: Long-lived (7 days), stored in HttpOnly secure cookie
- **CSRF Protection**: Double-submit pattern (refresh cookie + X-CSRF-Token header)
- **Password Hashing**: bcrypt with 12-round cost (~250ms)
- **Token Type**: JWT with `sub`, `type`, `jti`, `scopes`, `iat`, `exp`

## PHASE 1 Deliverables

✅ **Dependencies & Configuration**
- `requirements.txt`: All pinned production dependencies
- `pyproject.toml`: Poetry manifest
- `src/core/config.py`: Pydantic v2 Settings with .env loading
- `.env.example`: Template with all required environment variables

✅ **Database & ORM**
- `src/core/database.py`: Async SQLAlchemy engine, AsyncSessionLocal, get_db dependency
- `src/shared/base_model.py`: Base + AuditableBase with UUID PKs, audit fields, TenantMixin

✅ **Shared Utilities**
- `src/shared/base_repository.py`: Generic CRUD repository (get, create, update, soft_delete)
- `src/shared/exceptions.py`: Custom exception hierarchy (ERPException, NotFoundError, etc.)
- `src/shared/response.py`: APIResponse wrapper for consistent JSON
- `src/shared/pagination.py`: OffsetPagination, CursorPagination schemas

✅ **Security & Authentication**
- `src/core/security.py`: Password hashing, JWT generation/validation, get_current_user dependency
- `src/modules/users/models.py`: User, Role, Permission, UserRole, RolePermission, PasswordResetToken
- `src/modules/users/schemas.py`: Pydantic schemas for requests/responses
- `src/modules/users/repository.py`: Database layer for User/Role/Permission queries
- `src/modules/users/services.py`: Business logic (create_user, change_password, etc.)
- `src/modules/users/routers.py`: API endpoints (/auth/login, /auth/refresh, /auth/me, etc.)

✅ **Application Entry Point**
- `src/main.py`: FastAPI app initialization, middleware (CORS, TrustedHost, GZip), router registration

## Next Steps (PHASE 2+)

- Alembic migrations for versioned schema changes
- Finance module: Chart of Accounts, Journal Entries, Fee Receipts
- M-Pesa Daraja integration: Payment processing
- Celery task queue for async operations (SMS, email, reports)
- Redis for caching, token revocation tracking
- Rate limiting (slowapi), audit logging
- Comprehensive test suite (pytest, testcontainers for DB/Redis)

## Troubleshooting

**ImportError: No module named 'src'**
- Run uvicorn from the `backend/` directory
- Ensure `PYTHONPATH` includes the backend root

**Database connection refused**
- Check PostgreSQL is running: `psql -U postgres`
- Verify `.env` database credentials

**"Could not validate credentials"**
- Ensure access token hasn't expired (30 min default)
- Check token format: "Bearer {token}"
- Verify SECRET_KEY matches between config and token issuer

## Documentation

- Architecture: `docs/backend-artifacts/ARCHITECTURE.md`
- Database Schema: `docs/backend-artifacts/DATABASE_SCHEMA.md`
- Security: `docs/backend-artifacts/SECURITY_GUIDE.md`
- Tech Stack: `docs/backend-artifacts/TECH_STACK.md`
