# Quizdesk Backend Service

FastAPI backend service for the Quizdesk institutional assessment platform.

---

## Prerequisites

- Python 3.11+ (Python 3.13 supported)
- Virtual environment at repository root (`.venv`)

---

## Setup & Execution (Windows PowerShell)

All commands should be executed from the repository root:

### 1. Activate Root Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `backend/.env` and supply your environment variables:
- `DATABASE_URL`: PostgreSQL connection URI.
- `SUPABASE_JWT_SECRET`: The JWT Secret from your Supabase Project Settings -> API.
- `SUPABASE_JWT_ALGORITHM`: Default is `HS256`.
- `SUPABASE_JWT_AUDIENCE`: Default is `authenticated`.

### 4. Run Development Server
```powershell
uvicorn app.main:app --app-dir backend --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

### 5. Run Test Suite
```powershell
python -m pytest -c backend/pytest.ini backend/tests -v
```

### 6. Database Migrations (Alembic)
Ensure the root virtual environment is activated:

- **Review Migration History**:
  ```powershell
  alembic -c backend/alembic.ini history
  ```

- **Generate Migration SQL (Offline Dry-Run)**:
  ```powershell
  alembic -c backend/alembic.ini upgrade head --sql
  ```

- **Apply Migrations to Target Database (Online)**:
  ```powershell
  alembic -c backend/alembic.ini upgrade head
  ```

- **Create a New Revision**:
  ```powershell
  alembic -c backend/alembic.ini revision -m "migration_description"
  ```


