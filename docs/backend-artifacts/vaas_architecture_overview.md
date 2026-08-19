# VaaS Platform - End-to-End Architecture Overview (Post-Refactor v0.2)

This document provides a holistic blueprint of the VaaS (Verification as a Service) platform, specifically targeted as a device-bound authentication and transaction-signing infrastructure for high-stakes industries like banking.

## 1. High-Level Architecture

The system follows a multi-tenant microservices architectural pattern, orchestrated centrally via an API Gateway and integrated with enterprise client systems.

### 1.1 Client Integration Tier (The SDKs)
*   **VaaS Client SDKs (iOS, Android, TypeScript):** *[Critical Gap Remediation]* Essential for bank integrations. Wraps WebAuthn and transaction signing APIs for seamless integration into the Bank's Mobile App.
*   **Console App (`apps/console`):** The primary user and tenant interface. Built using React + Vite.
*   **Admin App (`apps/admin`):** The platform administration portal.

### 1.2 Enterprise Integration & Identity
*   **Core Banking System (CBS) Webhooks:** VaaS acts as the authentication layer, firing secure webhooks to the Bank's CBS for transaction execution upon successful WYSIWYS signature validation.
*   **OIDC / SSO Federation & SCIM:** *[Enterprise Requirement]* IdP integration (e.g., Azure AD, Okta) for workforce identity, replacing basic internal user management.

### 1.3 Middleware Tier (API Gateway)
*   **API Gateway (`services/api-gateway`):** Acts as the strict ingress for all microservices. 
    *   **Responsibilities:** OPA-based policy enforcement, JWT blocklist checking, request routing, distributed tracing injection (OpenTelemetry), and rate limiting.

### 1.4 Backend Tier (Microservices)
*   **Auth Service (`services/auth-service`):** Manages identity, FIDO2/WebAuthn enrollment (ECDSA P-256), step-up MFA, and JWT issuance.
*   **Device Service (`services/device-service`):** Handles device integrity verification (Google Play Integrity, Apple App Attest).
*   **Spatial Service (`services/spatial-service`):** Manages geolocation features via PostGIS.
*   **Incident Service (`services/incident-service`):** Tracks fraud signals, risk rules, and alerts.
*   **Audit Service (`services/audit-service`):** Maintains a hash-chained, tamper-evident, append-only ledger of WebAuthn ceremonies and `TRANSACTION_SIGNED` events.
*   **Billing Service (`services/billing-service`):** Tracks usage and tenant API metering.

### 1.5 Data Tier
*   **PostgreSQL (with PostGIS):** Primary DB with strict Row-Level Security (RLS) and `withTenantContext()` isolation.
*   **Redis:** Ephemeral state (OPA policies, JWT blocklist, rate limits).

> [!WARNING]
> **Agent Limitations:** I cannot natively build the client SDKs in this pure documentation pass, nor can I execute the required SOC 2 Type II or FIDO Alliance certifications. These must be driven by your engineering and compliance teams using these blueprints.
