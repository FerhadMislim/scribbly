# Backend

FastAPI application providing REST API for Scribbly.

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 16
- Redis 7

### Setup

```bash
# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

## Project Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI application entry
│   ├── config.py         # Settings via pydantic-settings
│   ├── database.py       # SQLAlchemy async session
│   ├── dependencies.py   # Shared dependencies (DI)
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── routers/         # API route modules
│   ├── services/        # Business logic layer
│   └── utils/           # Shared utilities
├── tests/               # Unit and integration tests
├── alembic/             # Database migrations
├── requirements.txt
└── .env.example
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pytest --cov=app --cov-report=term-missing
```
