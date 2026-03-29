# Scribbly System Architecture Document

> **Project:** Scribbly — Multi-Platform AI Creative Tool for Kids  
> **Version:** 1.0.0  
> **Date:** 2026-03-29  
> **Status:** Draft — Pending Team Lead Approval

---

## 1. Executive Summary

Scribbly is a multi-platform AI-powered creative tool that transforms children's drawings into stylized artwork using Stable Diffusion, ControlNet, and LoRA models. The system comprises a React web frontend, SwiftUI iOS app, FastAPI backend, GPU-accelerated AI inference engine, and cloud storage.

---

## 2. System Context (C4 Level 1)

```mermaid
flowchart TB
    subgraph External
        U["Parents & Children"]
        AI["AI Model Providers<br/>(HuggingFace)"]
        Cloud["Cloud Infrastructure<br/>(AWS/Fly.io)"]
    end
    
    subgraph Scribbly
        Web["React Web App"]
        iOS["iOS App"]
        API["FastAPI Backend"]
        AIEngine["AI Inference Engine"]
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Storage[(S3/MinIO)]
        Queue[("Celery Queue")]
    end
    
    U -->|Uses| Web
    U -->|Uses| iOS
    Web -->|HTTPS| API
    iOS -->|HTTPS| API
    API --> AIEngine
    AIEngine --> Queue
    Queue --> AIEngine
    API --> DB
    API --> Cache
    API --> Storage
    AIEngine --> Storage
    AIEngine -->|Downloads Models| AI
```

---

## 3. Container Diagram (C4 Level 2)

```mermaid
flowchart TB
    subgraph Clients
        Web["React Web<br/>(Vite + TS)"]
        iOS["iOS App<br/>(SwiftUI)"]
    end
    
    subgraph API_Gateway["API Layer"]
        FastAPI["FastAPI<br/>(Port 8000)"]
        Auth["Auth Service<br/>(JWT)"]
        Router["API Router<br/>(/api/v1/)"]
    end
    
    subgraph Services["Services Layer"]
        Upload["Upload Service"]
        Generate["Generation Service"]
        Gallery["Gallery Service"]
        User["User Service"]
    end
    
    subgraph Storage_Layer["Storage Layer"]
        S3["S3/MinIO"]
        Postgres["PostgreSQL"]
        Redis["Redis"]
    end
    
    subgraph Inference["AI Inference Layer"]
        Celery["Celery Workers"]
        Pipeline["Inference Pipeline"]
        ControlNet["ControlNet + SDXL"]
    end
    
    Web -->|HTTPS| FastAPI
    iOS -->|HTTPS| FastAPI
    FastAPI --> Auth
    FastAPI --> Router
    Router --> Upload
    Router --> Generate
    Router --> Gallery
    Router --> User
    Upload --> S3
    Upload --> Postgres
    Generate --> Celery
    Generate --> Postgres
    Gallery --> Postgres
    Gallery --> S3
    User --> Postgres
    Celery --> Pipeline
    Pipeline --> ControlNet
    Pipeline --> S3
```

---

## 4. Component Diagrams

### 4.1 API Backend Components

```mermaid
flowchart LR
    subgraph API
        Main["main.py<br/>(FastAPI App)"]
        Config["config.py<br/>(Settings)"]
        Deps["dependencies.py<br/>(DI)"]
    end
    
    subgraph Routers
        AuthR["auth.py"]
        UploadR["upload.py"]
        GenerateR["generate.py"]
        TaskR["tasks.py"]
        UserR["user.py"]
    end
    
    subgraph Services
        AuthS["AuthService"]
        StorageS["StorageService"]
        TaskS["TaskService"]
    end
    
    subgraph Models
        SQLAlchemy["SQLAlchemy<br/>(Async)"]
        Pydantic["Pydantic<br/>(Schemas)"]
    end
    
    Main --> Config
    Main --> Deps
    Deps --> AuthR
    Deps --> UploadR
    Deps --> GenerateR
    Deps --> TaskR
    Deps --> UserR
    AuthR --> AuthS
    UploadR --> StorageS
    GenerateR --> TaskS
    TaskR --> TaskS
    UserR --> AuthS
    AuthS --> SQLAlchemy
    StorageS --> Pydantic
    TaskS --> SQLAlchemy
```

### 4.2 AI Inference Pipeline Components

```mermaid
flowchart TB
    subgraph Pipeline["Inference Pipeline"]
        Input["Input Image"]
        Preprocess["Preprocessor<br/>(OpenCV/HED)"]
        ControlNet["ControlNet<br/>(Canny/Scribble)"]
        SDXL["SDXL 1.0<br/>(Diffusers)"]
        LoRA["LoRA Manager"]
        Output["Output Image"]
    end
    
    subgraph Models
        SDXL_Model["SDXL Base Model"]
        CN_Canny["ControlNet Canny"]
        CN_Scribble["ControlNet Scribble"]
        LoRA_Weights["LoRA Weights"]
    end
    
    Input --> Preprocess
    Preprocess --> ControlNet
    ControlNet --> SDXL
    SDXL_Model --> SDXL
    CN_Canny --> ControlNet
    CN_Scribble --> ControlNet
    LoRA --> SDXL
    LoRA_Weights --> LoRA
    SDXL --> Output
```

---

## 5. Data Flow Diagrams

### 5.1 Image Generation Flow

```mermaid
sequenceDiagram
    participant User
    participant Web/iOS
    participant API
    participant DB
    participant S3
    participant Celery
    participant GPU

    User->>Web/iOS: Upload drawing
    Web/iOS->>API: POST /api/v1/artwork/upload
    API->>S3: Upload file
    S3-->>API: Success
    API->>DB: Record upload metadata
    DB-->>API: Success
    API-->>Web/iOS: { upload_id, preview_url }
    
    User->>Web/iOS: Select style & generate
    Web/iOS->>API: POST /api/v1/generate/image
    API->>DB: Create generation record
    DB-->>API: { task_id }
    API->>Celery: Queue inference task
    Celery-->>API: { task_id, status: queued }
    API-->>Web/iOS: { task_id, poll_url }
    
    loop Poll every 3s
        Web/iOS->>API: GET /api/v1/tasks/{task_id}
        API->>DB: Check task status
        DB-->>API: status
        API-->>Web/iOS: { status }
    end
    
    Celery->>GPU: Execute inference
    GPU->>S3: Upload result
    S3-->>GPU: Success
    GPU->>DB: Update task status = complete
    DB-->>GPU: Success
    
    Web/iOS->>API: GET /api/v1/tasks/{task_id}
    API->>DB: Get result URL
    DB-->>API: { result_url }
    API-->>Web/iOS: { status: complete, result_url }
    User->>Web/iOS: View & download result
```

### 5.2 Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Client
    participant API
    participant DB
    participant Redis

    User->>Client: Enter email/password
    Client->>API: POST /api/v1/auth/login
    API->>DB: Verify credentials
    DB-->>API: User found
    API->>Redis: Store refresh token
    API-->>Client: { access_token, refresh_token }
    Client->>Client: Store tokens
    
    Note over Client,API: Every request
    Client->>API: GET /api/v1/... + Authorization: Bearer {access_token}
    API->>API: Validate JWT
    API-->>Client: Response
    
    Note over Client,API: Token expired
    Client->>API: POST /api/v1/auth/refresh
    API->>Redis: Verify refresh token
    API-->>Client: { new_access_token }
```

---

## 6. API Specification

### 6.1 API Versioning Strategy

- **Base URL:** `https://api.scribbly.app/api/v1/`
- **Versioning:** URL path (`/api/v1/`)
- **Deprecation:** 6-month notice via headers and docs

### 6.2 Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, get tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Invalidate refresh token |
| POST | `/artwork/upload` | Upload drawing |
| POST | `/generate/image` | Generate styled image |
| POST | `/generate/animation` | Generate animation |
| GET | `/tasks/{task_id}` | Get task status |
| GET | `/gallery` | List user generations |
| GET | `/users/me/usage` | Get usage stats |
| GET | `/styles` | List available styles |

### 6.3 Request/Response Formats

```json
// POST /api/v1/generate/image
Request:
{
  "upload_id": "uuid",
  "style_id": "pixar_3d",
  "custom_prompt": "optional override"
}

Response (immediate):
{
  "task_id": "uuid",
  "status": "queued",
  "poll_url": "/api/v1/tasks/{task_id}"
}

Response (GET /tasks/{task_id}):
{
  "task_id": "uuid",
  "status": "complete",
  "result_url": "https://...",
  "created_at": "2026-03-29T10:00:00Z",
  "completed_at": "2026-03-29T10:00:45Z"
}
```

---

## 7. Infrastructure

### 7.1 Environment Tiers

| Tier | Purpose | URL | Database |
|------|---------|-----|----------|
| `local` | Development | localhost:3000 | SQLite |
| `staging` | Pre-production | staging.scribbly.app | PostgreSQL (staging) |
| `production` | Live | api.scribbly.app | PostgreSQL (production) |

### 7.2 Service Deployment

| Service | Platform | Instance Type | GPU |
|---------|----------|---------------|-----|
| FastAPI Backend | Fly.io | 2x CPU | No |
| AI Inference | AWS EC2 | g4dn.xlarge | NVIDIA T4 |
| PostgreSQL | Supabase/CloudSQL | Standard | N/A |
| Redis | Redis Cloud | 100MB | N/A |
| S3 Storage | AWS S3 / MinIO | Standard | N/A |
| Web Frontend | Vercel | Serverless | N/A |
| iOS App | App Store | N/A | N/A |

### 7.3 GPU Specifications

- **Model:** NVIDIA T4 (AWS g4dn.xlarge) or RTX 3090 (local development)
- **VRAM:** 16GB (T4) / 24GB (3090)
- **SDXL Requirements:** ~10GB VRAM
- **ControlNet Overhead:** ~2GB additional
- **Maximum Concurrent Inferences:** 1 per T4, 2 per 3090

---

## 8. Security

### 8.1 Authentication

- **Access Token:** JWT, 15-minute expiry, HS256
- **Refresh Token:** 7-day expiry, stored hashed in Redis
- **Password:** Bcrypt with cost factor 12

### 8.2 Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 5 requests/minute per IP |
| `/generate/*` | 10 requests/day (free tier) |
| All other | 100 requests/minute per IP |

### 8.3 Data Protection

- All S3 URLs signed with 1-hour expiry
- GPU inference server not publicly exposed (VPC only)
- Input validation on all endpoints
- Content safety filtering on prompts

---

## 9. Technical Stack Summary

| Layer | Technology |
|-------|-------------|
| Web Frontend | React 18, TypeScript, Vite, TailwindCSS |
| iOS App | Swift 5.9, SwiftUI |
| API Backend | FastAPI, Python 3.11, SQLAlchemy (async) |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| Storage | S3 / MinIO |
| AI Framework | PyTorch 2.1, Diffusers, ControlNet |
| Task Queue | Celery + Redis |
| CI/CD | GitHub Actions |
| Deployment | Fly.io, Vercel, AWS |

---

## 10. Approval

| Role | Name | Status | Date |
|------|------|--------|------|
| Tech Lead / Architect | | Pending | |
| Backend Lead | | Pending | |
| Frontend Lead | | Pending | |
| iOS Lead | | Pending | |
| AI Engineer | | Pending | |

---

*Document Version: 1.0.0*  
*Last Updated: 2026-03-29*
