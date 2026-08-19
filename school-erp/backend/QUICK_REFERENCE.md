# PHASE 1: Quick Reference Card

## 🚀 Quick Start (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create environment file
cp .env.example .env
# Edit .env with your local PostgreSQL/Redis credentials

# 3. Run development server
python -m uvicorn src.main:app --reload

# 4. Open API docs
# Browser: http://localhost:8000/api/v1/docs
```

---

## 🔐 Authentication Flow

### Login → Access Token + Cookies
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@school.edu",
  "password": "SecurePassword123!"
}

# Response
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGci...",
    "token_type": "bearer"
  }
}

# Cookies set automatically:
# - refresh_token (HttpOnly, Secure)
# - csrf_token (readable)
```

### Use Access Token
```bash
GET /api/v1/auth/me
Authorization: Bearer {access_token}

# Returns current user profile
```

### Refresh Token (rotate)
```bash
POST /api/v1/auth/refresh
X-CSRF-Token: {csrf_token}
Cookie: refresh_token={refresh_token}; csrf_token={csrf_token}

# Response: new access_token (old jti revoked)
```

### Logout
```bash
POST /api/v1/auth/logout

# Cookies cleared
```

---

## 📁 File Structure for New Modules

To add a new domain module (e.g., Finance), follow this pattern:

```
src/modules/finance/
├── __init__.py
├── models.py          # SQLAlchemy models
├── schemas.py         # Pydantic request/response
├── repository.py      # Database queries
├── services.py        # Business logic
└── routers.py         # API endpoints
```

### Models Template
```python
from src.shared.base_model import AuditableBase, TenantMixin, GUID, FK_UUID, SCHOOL_ID
from sqlalchemy.orm import Mapped

class Account(AuditableBase, TenantMixin):
    __tablename__ = "accounts"
    
    code: Mapped[str]
    name: Mapped[str]
    # ... rest of fields
```

### Repository Template
```python
from src.shared.base_repository import BaseRepository

class AccountRepository(BaseRepository[Account]):
    def __init__(self, db: AsyncSession):
        super().__init__(Account, db)
    
    async def custom_query(self):
        # Add domain-specific queries
        pass
```

### Service Template
```python
class AccountService:
    def __init__(self, db: AsyncSession):
        self.repo = AccountRepository(db)
    
    async def create_account(self, account_in: AccountCreate) -> AccountSchema:
        # Business logic here
        obj = await self.repo.create({...})
        await self.db.commit()
        return AccountSchema.model_validate(obj)
```

### Router Template
```python
from fastapi import APIRouter, Depends
from src.core.database import get_db
from src.modules.finance.services import AccountService
from src.shared.response import APIResponse

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("")
async def create_account(
    req: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
) -> APIResponse[AccountSchema]:
    service = AccountService(db)
    obj = await service.create_account(req)
    return APIResponse.success(data=obj)
```

### Wire into Main App
```python
# src/main.py
from src.modules.finance.routers import router as finance_router

app.include_router(finance_router, prefix=settings.API_V1_STR)
```

---

## 🔑 Key Patterns

### Base Repository CRUD
```python
user_repo = UserRepository(db)

# Read
user = await user_repo.get_by_id(user_id)
users, total = await user_repo.get_all_with_count(skip=0, limit=10)

# Create
user = await user_repo.create({"username": "john", "email": "john@school.edu", ...})
await db.commit()

# Update
user = await user_repo.update(user_id, {"is_active": False})
await db.commit()

# Soft Delete
await user_repo.soft_delete(user_id)
await db.commit()
```

### Dependency Injection
```python
async def my_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[MySchema]:
    service = MyService(db)
    result = await service.do_something(current_user.id)
    return APIResponse.success(data=result)
```

### Exception Handling
```python
from src.shared.exceptions import NotFoundError, ValidationError

async def get_user(user_id: UUID) -> UserSchema:
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")
    
    if not user.is_active:
        raise ValidationError("User is inactive")
    
    return UserSchema.model_validate(user)
```

### Password Policy
```python
from src.modules.users.services import UserService

service = UserService(db)
try:
    service._validate_password("MyPassword123!")
except ValidationError as e:
    # 12+ chars, 3 of 4 char classes required
    print(e.detail)
```

---

## 🔒 Security Config (.env)

**Generate secrets:**
```bash
# JWT signing key
openssl rand -hex 32

# Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Critical fields in .env:**
```env
ENVIRONMENT=development
SECRET_KEY=<your-32-char-hex>
ENCRYPTION_KEY=<your-fernet-key>
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=school_erp_db
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## 📊 Database Tables (PHASE 1)

```sql
-- User Management
users (id, school_id, username, email, password_hash, is_active, ...)
roles (id, school_id, name, is_system_role, ...)
permissions (id, name, module, ...)
user_roles (user_id, role_id)
role_permissions (role_id, permission_id)
password_reset_tokens (id, user_id, token, expires_at, used_at)
```

All inherit `created_at`, `updated_at`, `is_deleted` from AuditableBase.

---

## 🧪 Testing Endpoints

```bash
# Health
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@school.edu","password":"SecurePassword123!"}'

# Get profile (replace TOKEN)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"

# Change password
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password":"Old123!","new_password":"New456!","confirm_password":"New456!"}'

# Logout
curl -X POST http://localhost:8000/api/v1/auth/logout
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| ImportError: No module named 'src' | Run `python -m uvicorn ...` from backend/ root |
| Database connection refused | Verify PostgreSQL running, check .env credentials |
| "Could not validate credentials" | Token expired? Check Bearer format, verify SECRET_KEY |
| "CORS error" | Check BACKEND_CORS_ORIGINS in .env (comma-separated) |
| "CSRF validation failed" | Cookie != Header? Refresh endpoint requires both |

---

## 📚 Documentation Files

- **SETUP.md** — Local development walkthrough
- **PHASE1_COMPLETION.md** — Detailed architecture & validation
- **FILES_INDEX.md** — Complete file manifest
- **docs/backend-artifacts/TECH_STACK.md** — Dependency justification
- **docs/backend-artifacts/ARCHITECTURE.md** — DDD & 4-layer patterns
- **docs/backend-artifacts/SECURITY_GUIDE.md** — JWT, RBAC, encryption
- **docs/backend-artifacts/DATABASE_SCHEMA.md** — All 25 modules schema

---

## ✨ Next Steps

1. ✅ PHASE 1 complete: Run `python -m uvicorn src.main:app --reload`
2. 📋 PHASE 2: Add Finance module (journal entries, accounts, fee allocation)
3. 🏫 PHASE 3: Add Academic module (grades, reports, subjects)
4. 💼 PHASE 4: Add HR/Payroll (employee records, statutory deductions)

Each follows the same pattern: Models → Schemas → Repository → Service → Router.
