# DevOps & Deployment Guide

This document covers the complete infrastructure, containerization, deployment, and testing setup for the system.

## 1. Docker Setup

### `Dockerfile`

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*
COPY . .
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
CMD ["gunicorn", "-c", "gunicorn.conf.py", "src.main:app"]
```

### `docker-compose.yml` (Local Development)

```yaml
version: '3.8'
services:
  app:
    build: .
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: erp_user
      POSTGRES_PASSWORD: erp_password
      POSTGRES_DB: erp_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U erp_user -d erp_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    command: redis-server --appendonly yes

  celery_worker:
    build: .
    command: celery -A src.core.celery_app worker -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - redis
      - db

  celery_beat:
    build: .
    command: celery -A src.core.celery_app beat -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - redis

  flower:
    build: .
    command: celery -A src.core.celery_app flower --port=5555
    ports:
      - "5555:5555"
    env_file:
      - .env
    depends_on:
      - redis
      - celery_worker

volumes:
  pgdata:
  redisdata:
```

## 2. Database Migrations with Alembic

### `alembic/env.py` (Async Support)

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from src.core.config import settings
from src.models.base import Base # Import your Base with all models loaded

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online():
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    pass # Add offline support if needed
else:
    run_migrations_online()
```

### Commands

- `alembic revision --autogenerate -m "Add accounts table"`
- `alembic upgrade head`
- `alembic downgrade -1`

## 3. Environment Management

### `pydantic-settings` Configuration

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "Construction & School ERP"
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Daraja API
    MPESA_CONSUMER_KEY: str
    MPESA_CONSUMER_SECRET: str
    MPESA_PASSKEY: str
    MPESA_SHORTCODE: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
```

## 4. CI/CD Pipeline (GitHub Actions)

### `.github/workflows/ci.yml`

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install ruff mypy pytest pytest-asyncio pytest-cov testcontainers
      - name: Lint with Ruff
        run: ruff check .
      - name: Type check with mypy
        run: mypy src/
      - name: Test with pytest
        run: pytest --cov=src tests/
        env:
          ENVIRONMENT: test
```

## 5. Production Server Setup

### `gunicorn.conf.py`

```python
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name erp.school.ac.ke;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name erp.school.ac.ke;

    ssl_certificate /etc/letsencrypt/live/erp.school.ac.ke/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.school.ac.ke/privkey.pem;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;

    # Gzip
    gzip on;
    gzip_types text/plain application/json;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 6. Celery Periodic Tasks

### `src/core/celery_app.py`

```python
from celery import Celery
from celery.schedules import crontab
from src.core.config import settings

celery_app = Celery(
    "erp_tasks",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL)
)

celery_app.conf.beat_schedule = {
    'daily_billing_run_status': {
        'task': 'src.tasks.billing.generate_status_report',
        'schedule': crontab(hour=23, minute=0),
    },
    'monthly_payroll_run': {
        'task': 'src.tasks.payroll.auto_run',
        'schedule': crontab(day_of_month='1', hour=1, minute=0),
    },
    'monthly_fee_arrears_sms': {
        'task': 'src.tasks.notifications.send_fee_arrears_reminders',
        'schedule': crontab(day_of_month='15', hour=8, minute=0),
    },
    'weekly_nemis_cache_refresh': {
        'task': 'src.tasks.compliance.refresh_nemis_cache',
        'schedule': crontab(day_of_week='sun', hour=2, minute=0),
    },
    'nightly_depreciation': {
        'task': 'src.tasks.finance.calculate_depreciation',
        'schedule': crontab(hour=3, minute=0),
    },
    'nightly_db_backup': {
        'task': 'src.tasks.system.trigger_db_backup',
        'schedule': crontab(hour=4, minute=0),
    }
}
celery_app.conf.timezone = 'Africa/Nairobi'
```

## 7. Testing Strategy

### `conftest.py`

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from testcontainers.postgres import PostgresContainer
from src.models.base import Base

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    with PostgresContainer("postgres:16-alpine") as postgres:
        engine = create_async_engine(
            postgres.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session(db_engine):
    async with AsyncSession(db_engine) as session:
        yield session
        await session.rollback()
```

### Example Unit Test (Payroll)

```python
import pytest
from decimal import Decimal
from src.services.payroll import PayrollEngine

@pytest.mark.asyncio
async def test_payroll_tax_band_edge_cases():
    basic_salary = Decimal('50000.00')
    allowances = Decimal('10000.00')
    
    result = await PayrollEngine.calculate_employee_payroll(basic_salary, allowances)
    
    assert result.gross_pay == Decimal('60000.00')
    assert result.nssf_deduction > 0
    assert result.paye_deduction > 0
    assert result.shif_deduction > 0
    assert result.housing_levy == Decimal('60000.00') * Decimal('0.015')
    assert result.net_pay == (result.gross_pay - result.paye_deduction - result.nssf_deduction - result.shif_deduction - result.housing_levy)
```

### Example Integration Test (M-Pesa)

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_mpesa_callback_endpoint():
    payload = {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "12345",
                "CheckoutRequestID": "67890",
                "ResultCode": 0,
                "ResultDesc": "Success",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 1000},
                        {"Name": "MpesaReceiptNumber", "Value": "RST12345"},
                        {"Name": "PhoneNumber", "Value": 254700000000}
                    ]
                }
            }
        }
    }
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/payments/mpesa/callback", json=payload)
    
    assert response.status_code == 200
```
