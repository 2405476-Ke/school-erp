# VaaS Production Database Schemas

**Status**: EXECUTION_READY  
**Authority**: VaaS Platform Constitution  
**Enforcement**: Flyway / Liquibase Migrations.

---

## 1. Physical Isolation & Tenancy Strategy

*   **Standard Tier**: Shared PostgreSQL Cluster. Logical isolation via `tenant_id` column + Indestructible Row Level Security (RLS).
*   **Banking Tier**: **Physically Separate** PostgreSQL Cluster. No shared resources.
*   **RPO=0 Mandate**: `synchronous_commit = on` (Local) + Multi-AZ Sync Replication.

---

## 2. Core Tables (DDL)

### A. Tenants (Root Entity)
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    tier VARCHAR(50) NOT NULL CHECK (tier IN ('STANDARD', 'BANKING')),
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    geo_scope VARCHAR(2)[] DEFAULT '{KE}', -- ISO 3166-1 alpha-2
    kms_key_arn VARCHAR(255), -- Tenant-specific Encryption Key
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenants_status ON tenants(status);
```

### B. Identities (Users & Principals)
```sql
CREATE TABLE identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    email_hash VARCHAR(64) NOT NULL, -- SHA-256 (Never store raw email here)
    pii_vault_ref VARCHAR(255), -- Pointer to PII Vault (Encrypted)
    password_hash VARCHAR(255), -- Argon2id (Null if FIDO2/SSO)
    mfa_enabled BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) NOT NULL DEFAULT 'USER',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Optimization: Composite index for Login Lookups
CREATE UNIQUE INDEX idx_identities_tenant_email ON identities(tenant_id, email_hash);
ALTER TABLE identities ENABLE ROW LEVEL SECURITY;
```

### C. Device Registry (Hardware Backed)
```sql
CREATE TABLE device_registry (
    device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    identity_id UUID REFERENCES identities(id),
    public_key_pem TEXT NOT NULL,
    attestation_data JSONB, -- Hardware/OS signals
    trust_score FLOAT DEFAULT 1.0,
    status VARCHAR(50) DEFAULT 'ACTIVE', -- ACTIVE, SUSPENDED, REVOKED
    last_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_device_lookup ON device_registry(tenant_id, device_id);
ALTER TABLE device_registry ENABLE ROW LEVEL SECURITY;
```

---

## 3. High-Volume Event Tables (Partitioned)

### D. Authentication Events (Login Attempts)
```sql
CREATE TABLE auth_events (
    event_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    identity_id UUID,
    event_type VARCHAR(50) NOT NULL, -- LOGIN_SUCCESS, LOGIN_FAIL, MFA_CHALLENGE
    ip_address INET NOT NULL,
    risk_score FLOAT,
    device_fingerprint VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Strategy: Monthly Partitions
CREATE TABLE auth_events_2026_01 PARTITION OF auth_events 
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX idx_auth_events_tenant_time ON auth_events(tenant_id, created_at DESC);
```

### E. Spatial Events (PostGIS)
```sql
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE spatial_events (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    device_id UUID NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    accuracy_meters FLOAT,
    is_spoofed BOOLEAN DEFAULT FALSE,
    geofence_status VARCHAR(50), -- INSIDE, OUTSIDE, UNKNOWN
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE spatial_events_2026_01 PARTITION OF spatial_events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Spatial Index on partitions usually needed, but BRIN often better for time-series geo
CREATE INDEX idx_spatial_events_brin ON spatial_events USING BRIN(created_at);
```

---

## 4. The Immutable Ledger (Audit)

**Rule**: Application Role (`app_user`) has `INSERT` only. No `UPDATE`, No `DELETE`.

```sql
CREATE TABLE audit_logs (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    actor_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL, -- e.g., 'POLICY_UPDATE'
    target_resource VARCHAR(255),
    changes JSONB, -- { "old": "...", "new": "..." }
    integrity_hash VARCHAR(64) NOT NULL, -- SHA-256(prev_hash + current_row)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Prevent Updates/Deletes via Trigge (Defense in Depth)
CREATE OR REPLACE FUNCTION prevent_modification() RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit Logs are Immutable!';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_immutable
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_modification();
```

---

## 5. Security & Isolation enforcement

### A. Row Level Security (RLS) Policy
The `current_setting('app.current_tenant')` is injected by the API Gateway at the connection pool level.

```sql
-- Generic Policy Template
CREATE POLICY tenant_isolation_policy ON identities
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

CREATE POLICY tenant_isolation_policy ON device_registry
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

### B. Encryption Boundaries
*   **Disk Level (AWS KMS)**: All EBS Volumes and RDS instances must be encrypted with `AES-256`.
*   **Field Level (Application Side)**:
    *   `identities.pii_vault_ref`: Content in Vault is encrypted.
    *   `device_registry.public_key_pem`: NOT encrypted (Public).
    *   `auth_events.ip_address`: NOT encrypted (Ops requirement), but Access Controlled.

---

## 6. Failure Modes

| Failure | Behavior |
| :--- | :--- |
| **Partition Missing** | Insert Fails (`Exception: no partition`). Monitoring must catch this 7 days in advance. |
| **RLS Context Missing** | Query returns 0 rows. (Fail Safe). |
| **Integrity Check** | Periodic job checks `integrity_hash` chain. Mismatch -> **P0 Incident**. |

