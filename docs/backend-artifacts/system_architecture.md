# Vaas System Architecture & Visuals

## 1. Device-Bound Authentication Workflow
This sequence details how a mobile device proves its hardware integrity to the Vaas platform using a nonce-based challenge-response mechanism.

```mermaid
sequenceDiagram
    participant App as Mobile App (SDK)
    participant GW as API Gateway
    participant Auth as Auth Service
    participant Redis as Redis (Nonce)
    participant Repo as Device/Audit Repo

    Note over App, Repo: Phase 1: Enrollment (One-Time)
    App->>GW: POST /devices/enroll/start {deviceId}
    GW->>Auth: Request Enrollment Challenge
    Auth->>Redis: Generate & Store Nonce (TTL 5m)
    Auth-->>App: Return Nonce
    
    App->>App: Sign Nonce with Hardware Key (TEE/StrongBox)
    App->>GW: POST /devices/enroll/complete {attestation}
    GW->>Auth: Verify Attestation
    Auth->>Redis: Retrieve & Validate Nonce
    Auth->>Auth: Verify Certificate Chain (Google Root CA)
    Auth->>App: Extract Public Key & Hardware Capability
    Auth->>Repo: Store Device Identity & Trust Tier
    Auth-->>App: Enrollment Success (Device ID)

    Note over App, Repo: Phase 2: Transaction Verification
    App->>GW: POST /transact {amount, receiver, signature}
    GW->>Auth: Verify Request Signature
    Auth->>Repo: Fetch Device Public Key
    Auth->>Auth: Verify Ed25519/RSA Signature
    Auth->>Repo: Check Device Status (Active/Revoked)
    Auth-->>GW: Token Valid & Device Trusted
    GW->>GW: Forward to Transaction Service
```

## 2. Spatial Verification Flow
Logic flow for determining if a user is operating within a trusted geofence.

```mermaid
flowchart TD
    A[Incoming Transaction Request] --> B{Contains GPS Data?}
    B -- No --> C[Reject: Missing Context]
    B -- Yes --> D[Extract Lat/Long & Accuracy]
    D --> E[Spatial Service: Point-in-Polygon Check]
    E --> F{Inside Allowed Zone?}
    F -- Yes --> G[Check Velocity/Speed]
    G --> H{Speed < Threshold?}
    H -- Yes --> I[Result: VERIFIED_SPATIAL]
    H -- No --> J[Result: SUSPICIOUS_VELOCITY]
    F -- No --> K[Result: GEOFENCE_VIOLATION]
    
    I --> L[Append to Trust Score]
    J --> L
    K --> L
```

## 3. Transaction Scoring & Immutable Ledger
How disparate data points are aggregated into a single Trust Score and permanently recorded.


```mermaid
graph LR
    subgraph Inputs
    D["Device Telemetry"]
    S["Spatial Context"]
    I["Identity/History"]
    end
    
    subgraph Processing
    PE[Policy Engine]
    end
    
    subgraph Output
    TS["Trust Score (0-100)"]
    DEC["Decision: ALLOW/BLOCK"]
    end
    
    subgraph Storage
    L[(Immutable Ledger)]
    end
    
    D --> PE
    S --> PE
    I --> PE
    
    PE --> TS
    TS --> DEC
    DEC --> L
    TS --> L
    L -.->|Audit Sync| Regulator[Regulator Node]
```

## 4. Cloud Infrastructure & OTP Integration
Deployment architecture on AWS/GCP and integration with Telco providers.


```mermaid
graph TB
    Client["Mobile SDK / Web Console"] --> CDN["Cloudflare / Load Balancer"]
    
    subgraph VPC [Private Cloud VPC]
        GW["API Gateway (Nginx/Fastify)"]
        
        subgraph Services
            Auth[Auth Service]
            Spatial[Spatial Service]
            Audit[Audit Service]
            OTP[OTP Engine]
        end
        
        subgraph Data
            Redis[(Redis Cache)]
            DB[(Postgres Cluster)]
        end
    end
    
    subgraph External
        AT["Africa's Talking API"]
        Maps["Google Maps / OSM"]
    end
    
    Client --> GW
    GW --> Auth
    GW --> Spatial
    GW --> Audit
    GW --> OTP
    
    Auth --> Redis
    Auth --> DB
    OTP --> AT
    Spatial --> Maps
    Spatial --> DB
    Audit --> DB
```

## 5. Trust Studio UI Concept (Wireframe)
Layout for the "Trust Studio" dashboard where operators manage risk.

```mermaid
graph TB
    subgraph Dashboard [Trust Studio Dashboard]
        direction TB
        
        subgraph Sidebar [Navigation Sidebar]
            Nav1["Dashboard"]
            Nav2["Users"]
            Nav3["Devices"]
            Nav4["Trust Rules"]
            Nav5["Audit Log"]
        end
        
        subgraph Main [Main Content Area]
            direction TB
            subgraph KPIs [Key Metrics Row]
                Card1["Active Alerts: 12"]
                Card2["Verified Volume: $45.2k"]
                Card3["Avg Risk Score: 12"]
            end
            
            subgraph MapSection [Visual Intelligence]
                MapWithPins["Live Threat Map <br/> (Leaflet Interactive)"]
            end
            
            subgraph TableSection [Security Events]
                Table["Recent Events Log <br/> Time | Device | Risk | Status"]
            end
            
            KPIs --> MapSection
            MapSection --> TableSection
        end
        
        Sidebar ~~~ Main
    end
    
    classDef container fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef card fill:#fff,stroke:#666,stroke-width:1px;
    
    class Dashboard,Sidebar,Main container;
    class Card1,Card2,Card3,MapWithPins,Table card;
```

## 6. OTP Service Internal Architecture
The OTP Service functions as a Policy Enforcement Point before dispatching messages.

```mermaid
graph TB
    Req["Incoming Request<br/>(Recipient, Tier, Context)"] --> Policy{"Policy Engine<br/>Check Tier Level"}
    
    Policy -- "Tier 1 (Standard)" --> Gen[Generate Token]
    
    Policy -- "Tier 2 (Geo-Fenced)" --> CheckGeo{Has Lat/Long?}
    CheckGeo -- Yes --> Gen
    CheckGeo -- No --> Block["BLOCK: Policy Violation<br/>(Missing Geo)"]
    
    Policy -- "Tier 3 (Device-Bound)" --> CheckDev{Device Trusted?}
    CheckDev -- Yes --> Gen
    CheckDev -- "No / Risk > 70" --> BlockDev["BLOCK: High Risk Device"]
    
    Gen --> Orch["Channel Orchestrator"]
    
    subgraph Dispatch [Dispatch Logic]
        direction TB
        Orch --> TrySMS["Attempt 1: SMS (Africa's Talking)"]
        TrySMS --> WaitDLR{Delivered?}
        WaitDLR -- Yes --> Log[Log Success]
        WaitDLR -- "No (Timeout/Fail)" --> TryWA["Attempt 2: WhatsApp (Fallback)"]
        TryWA --> Log
    end
```
