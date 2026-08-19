# Kenya Secondary School ERP - Technology Stack Decision Document

## 1. Core Stack Justification

The backend architecture is built upon a modern, high-performance, asynchronous Python stack. The specific choices are tailored for the demands of an Enterprise Resource Planning (ERP) system deployed in the Kenyan context, supporting complex relational data, external integrations (Daraja API, SMS gateways), and high concurrency during peak times (e.g., term opening fee payments).

### Why FastAPI over Django/Flask?
- **High Performance:** Built on Starlette and Pydantic, FastAPI is one of the fastest Python frameworks available, matching the performance of Node.js and Go. This is critical for handling concurrent M-Pesa callbacks and high volumes of teacher data entry during exam periods.
- **Native Async Support:** Seamless asynchronous operations, allowing non-blocking I/O when integrating with external APIs like Daraja (M-Pesa) or sending bulk SMS via Africa's Talking.
- **Automatic API Documentation:** Native OpenAPI 3.1 support out of the box, facilitating rapid integration with frontend applications (React/Next.js) or mobile apps.
- **Data Validation:** Pydantic v2 ensures strict data validation and serialization at the edge, reducing bugs related to invalid input (e.g., malformed M-Pesa phone numbers or invalid KES amounts).

### Why PostgreSQL over MySQL?
- **Advanced Data Types:** Native support for `JSONB`, `UUID`, and arrays. `JSONB` is essential for storing flexible data like raw M-Pesa callback payloads or dynamic report card configurations.
- **Concurrency and ACID Compliance:** Superior handling of complex transactions, which is non-negotiable for the Finance module (double-entry accounting, fee allocation, PAYE calculations).
- **Extensibility:** Support for advanced indexing and extensions, scaling better with complex queries required by NEMIS/KEMIS reporting.

### Why SQLAlchemy 2.0 Async?
- **Modern ORM:** The 2.0 style completely separates the Unit of Work and connection pooling, offering a true async experience with `asyncpg`.
- **Type Safety:** Improved typing support aligns perfectly with Mypy and IDE autocompletion, reducing developer errors.
- **Performance:** Async session management minimizes thread-blocking during heavy database operations.

### Why Pydantic v2?
- **Rust Core:** Up to 50x faster validation than v1, which directly translates to lower latency in API requests.
- **Strict Typing:** Provides absolute confidence in the structure of requests and responses.

---

## 2. Full Dependency Manifest

### `pyproject.toml`
```toml
[tool.poetry]
name = "kenya-school-erp"
version = "1.0.0"
description = "Enterprise Resource Planning system for Kenyan Secondary Schools"
authors = ["Engineering Team"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "0.109.2"
uvicorn = {extras = ["standard"], version = "0.27.1"}
gunicorn = "21.2.0"
sqlalchemy = "2.0.25"
asyncpg = "0.29.0"
alembic = "1.13.1"
pydantic = "2.6.1"
pydantic-settings = "2.1.0"
redis = "5.0.1"
celery = {extras = ["redis"], version = "5.3.6"}
httpx = "0.26.0"
python-jose = {extras = ["cryptography"], version = "3.3.0"}
passlib = {extras = ["bcrypt"], version = "1.7.4"}
python-multipart = "0.0.9"
weasyprint = "61.1"
Jinja2 = "3.1.3"
phonenumbers = "8.13.29"

[tool.poetry.group.dev.dependencies]
pytest = "8.0.0"
pytest-asyncio = "0.23.5"
testcontainers = "3.7.1"
ruff = "0.2.1"
black = "24.1.1"
mypy = "1.8.0"
httpx = "0.26.0"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 100
select = ["E", "F", "I"]

[tool.black]
line-length = 100
target-version = ['py311']
```

### `requirements.txt`
```text
fastapi==0.109.2
uvicorn[standard]==0.27.1
gunicorn==21.2.0
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.6.1
pydantic-settings==2.1.0
redis==5.0.1
celery[redis]==5.3.6
httpx==0.26.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
weasyprint==61.1
Jinja2==3.1.3
phonenumbers==8.13.29
```

---

## 3. Project Directory Structure

```text
kenya-school-erp/
├── alembic/
│   ├── versions/
│   └── env.py
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── entrypoint.sh
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Pydantic BaseSettings
│   │   ├── database.py        # Async engine & session maker
│   │   ├── security.py        # JWT generation, password hashing
│   │   ├── exceptions.py      # Custom exception handlers
│   │   ├── logging.py         # Structured JSON logging
│   │   └── middleware.py      # CORS, Request ID, Timing
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── base_model.py      # SQLAlchemy Base (UUID, timestamps)
│   │   ├── base_repository.py # Generic CRUD ops
│   │   ├── base_service.py
│   │   ├── pagination.py      # Cursor & Offset schemas
│   │   └── response.py        # Standardized API wrappers
│   ├── modules/
│   │   ├── academics/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── services.py
│   │   │   ├── routers.py
│   │   │   └── tasks.py
│   │   ├── admissions/
│   │   ├── boarding/
│   │   ├── communication/
│   │   ├── finance/
│   │   │   ├── mpesa/
│   │   │   │   ├── daraja_client.py
│   │   │   │   └── callbacks.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── routers.py
│   │   ├── hr/
│   │   └── inventory/
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── celery_app.py      # Celery instance configuration
│   │   └── schedules.py       # Cron tasks (e.g., midnight backups)
│   ├── main.py                # FastAPI application factory
├── tests/
│   ├── conftest.py
│   ├── core/
│   ├── finance/
│   └── hr/
├── .env.example
├── alembic.ini
├── pyproject.toml
└── requirements.txt
```

---

## 4. Environment Configuration (`.env.example`)

```env
# Application Settings
PROJECT_NAME="Kenya Secondary School ERP"
ENVIRONMENT=development
API_V1_STR=/api/v1
DEBUG=True

# Security
# Generate using: openssl rand -hex 32
SECRET_KEY=replace_with_secure_hex_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Connection
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=erp_password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=school_erp_db
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}

# Redis & Celery
REDIS_HOST=localhost
REDIS_PORT=6379
CELERY_BROKER_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0
CELERY_RESULT_BACKEND=redis://${REDIS_HOST}:${REDIS_PORT}/1
CACHE_URL=redis://${REDIS_HOST}:${REDIS_PORT}/2

# M-Pesa Daraja API Integration
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_PASSKEY=your_passkey
MPESA_SHORTCODE=174379
MPESA_EXPRESS_CALLBACK_URL=https://api.yourschool.co.ke/api/v1/finance/mpesa/callback

# Africa's Talking / SMS Gateway
SMS_PROVIDER=africastalking
AT_USERNAME=your_username
AT_API_KEY=your_api_key
SENDER_ID=YOUR_SCHOOL

# Admin Defaults
FIRST_SUPERUSER=admin@school.co.ke
FIRST_SUPERUSER_PASSWORD=secure_initial_password
```

---

## 5. Core Configuration Class (`src/core/config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, validator, PostgresDsn, Field
from typing import Optional, List, Union

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Kenya Secondary School ERP"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Security
    SECRET_KEY: str = Field(..., description="JWT Secret Key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=str(values.get("POSTGRES_PORT")),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # M-Pesa Daraja
    MPESA_ENVIRONMENT: str = "sandbox"
    MPESA_CONSUMER_KEY: str
    MPESA_CONSUMER_SECRET: str
    MPESA_PASSKEY: str
    MPESA_SHORTCODE: str
    MPESA_EXPRESS_CALLBACK_URL: AnyHttpUrl

    # Africa's Talking
    SMS_PROVIDER: str = "africastalking"
    AT_USERNAME: str
    AT_API_KEY: str
    SENDER_ID: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
```
