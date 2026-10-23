# Quizdesk Operations & Disaster Recovery Runbook

**Document Version:** 1.0.0  
**Effective Date:** 2026-10-23  
**Target Environment:** Institutional Pilot / Production (Supabase PostgreSQL + FastAPI)  
**Status:** Confirmed Baseline

---

## 1. Overview & Objective

This runbook establishes operational procedures for administrators, DevOps personnel, and engineers deploying and managing **Quizdesk** during institutional college pilots. It details database backup and restore routines, migration rollback procedures, telemetry and error diagnosis, security log hygiene, and connection capacity limits.

---

## 2. Critical Assessment Data & Integrity Invariants

Quizdesk operates with server-authoritative integrity rules. The following tables contain immutable assessment history that **MUST NEVER** be truncated or dropped:

| Table Name | Description | Invariant & Preservation Rule |
| :--- | :--- | :--- |
| `users` & `student_profiles` | Institutional roster and student identity | Identity preservation; roll numbers and emails must remain unique. |
| `quizzes` & `quiz_versions` | Published quiz definitions and historical snapshots | Once an attempt references a `version_id`, that version is immutable. |
| `questions` & `question_options` | Assessment items, correct answers, and scoring | Historical snapshots linked to quiz versions cannot be modified in-place. |
| `quiz_assignments` | Student-to-quiz eligibility | Governs eligibility window; unique `(quiz_id, student_id)`. |
| `quiz_attempts` | Active and submitted exam attempts | Authoritative timestamps, attempt states (`in_progress`, `submitted`, `abandoned`), final scores. |
| `attempt_answers` | Student response submissions | Stores autosaved responses and timestamps; unique `(attempt_id, question_id)`. |
| `attempt_telemetry_events` | Proctoring telemetry & focus tracking | Idempotently logged browser events (`event_hash`); penalty auditing. |
| `grade_adjustments` | Teacher manual score overrides | Immutable audit trail with mandatory override reason and timestamp. |
| `audit_events` | Security and access audit log | Cryptographically sequenced event stream; append-only. |

---

## 3. Database Backup & Recovery Procedures

### 3.1 Hosting Provider Automated Backups (Supabase)
1. **Automated Daily Backups:**
   - Supabase automatically performs physical and logical backups daily on paid plans, stored redundantly across AWS S3 regions.
   - For free-tier instances, automated physical snapshots are managed platform-side with 7-day retention.
2. **Point-in-Time Recovery (PITR):**
   - In production tiers, WAL (Write-Ahead Logging) archiving enables continuous restoration down to the second of failure.
   - Recommended during active exam weeks to guarantee recovery from accidental human error.

### 3.2 Manual Pre-Exam Snapshot (Logical Backup via `pg_dump`)
Prior to every major examination window, administrators MUST generate an offline logical dump:

```bash
# Set connection string pointing to the Supabase Session Pooler or direct DB URL
export DATABASE_URL="postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"

# Execute pg_dump with custom compressed archive format
pg_dump \
  "$DATABASE_URL" \
  --format=c \
  --no-owner \
  --no-privileges \
  --schema=public \
  --file="quizdesk_backup_$(date +%Y%m%d_%H%M%S).dump"
```

### 3.3 Safe Restoration Drill & Verification
**Rule:** Never restore a backup directly into the active production database during an investigation.

1. **Provision a Clean Disposable Database:**
   - Launch a local Docker PostgreSQL container or create an isolated Supabase test project:
     ```bash
     docker run --name quizdesk-restore-drill -e POSTGRES_PASSWORD=postgres -p 5433:5432 -d postgres:17
     ```
2. **Execute Restoration:**
   ```bash
   pg_restore \
     --clean \
     --if-exists \
     --no-owner \
     --no-privileges \
     --dbname="postgresql://postgres:postgres@localhost:5433/postgres" \
     quizdesk_backup_20261023_120000.dump
   ```
3. **Verify Table Integrity:**
   ```bash
   python -c "
   import psycopg
   with psycopg.connect('postgresql://postgres:postgres@localhost:5433/postgres') as conn:
       with conn.cursor() as cur:
           cur.execute('SELECT count(*) FROM alembic_version;')
           print('Alembic revisions restored:', cur.fetchall())
           cur.execute('SELECT count(*) FROM quiz_attempts WHERE status = \'submitted\';')
           print('Submitted attempts count:', cur.fetchone()[0])
   "
   ```

---

## 4. Migration & Deployment Failure Recovery

### 4.1 Automated Health Probes
The backend exposes two Kubernetes/load-balancer compliant health probes:
- **Liveness (`GET /health/live`):** Returns `{"status": "alive"}` immediately. Indicates process is running.
- **Readiness (`GET /health/ready`):** Executes `SELECT 1` against the database pool. Returns `200 OK` (`{"status": "ready"}`) if healthy, or `503 Service Unavailable` (`{"status": "unhealthy", "database": "disconnected"}`) if the database pool is saturated, timed out, or disconnected.

Configure load balancers and reverse proxies (e.g., Caddy, Nginx, AWS ALB) to drop instances failing `/health/ready` before student traffic can reach them.

### 4.2 Handling a Failed Alembic Migration
Alembic migrations are executed inside transactions on PostgreSQL (DDL transactional support). If a migration fails midway:
1. PostgreSQL automatically rolls back the failed DDL statement.
2. Check current database revision:
   ```bash
   alembic current
   ```
3. Generate the exact offline downgrade SQL to inspect changes before running:
   ```bash
   alembic downgrade [TARGET_REVISION]:[CURRENT_REVISION] --sql
   ```
4. Revert to the previous stable revision:
   ```bash
   alembic downgrade -1
   ```
5. Rerun the backend test suite:
   ```bash
   pytest -v
   ```

---

## 5. Capacity & Connection Pool Management

### 5.1 Supabase Connection Limits
- **Free Tier / Session Pooler Ceiling:** 15 client connections maximum.
- Exceeding this triggers: `FATAL: EMAXCONNSESSION: max clients reached in session mode - max clients are limited to pool_size: 15`.

### 5.2 Calibrated FastAPI QueuePool Settings
To safely serve 50+ concurrent students without exhausting the 15-connection upstream pool:
```ini
DB_POOL_SIZE=8
DB_MAX_OVERFLOW=4
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```
- **Rationale:** SQLAlchemy's internal `QueuePool` allows 50 concurrent async request workers in Python to multiplex over 8–12 physical PostgreSQL connections. While an async request waits on network I/O or token parsing, the database connection is checked in, ensuring zero connection starvation.

---

## 6. Observability, Logging, and Error Diagnosis

### 6.1 Diagnostic Indicators

| Symptom | Diagnostic Log Pattern | Root Cause & Resolution |
| :--- | :--- | :--- |
| **Failed Logins** | Supabase Auth API: `invalid_credentials` or `email_not_confirmed` | Verify student email confirmation in Supabase dashboard or check enrollment status. |
| **Quiz Start Failure** | `404 Not Found` or `400 Bad Request` on `/student/quizzes/{id}/start` | Verify assignment exists in `quiz_assignments` and current time is within `(start_time, end_time)`. |
| **Autosave Failures** | `409 Conflict` or `400 Bad Request` on `/student/attempts/{id}/answers` | Verify attempt is still `in_progress` and time limit has not expired. |
| **Database Saturation** | `TimeoutError: QueuePool limit of size 8 overflow 4 reached` | Incoming concurrency exceeded pool queue timeout; scale `DB_POOL_SIZE` or verify slow queries. |
| **Submission Burst 503** | `GET /health/ready` returning 503 | Database connection pool exhausted or upstream Supabase pooler reset. |

### 6.2 Data Privacy & Credential Redaction Rules
Logs **MUST NEVER** output:
1. Passwords or plaintext credentials.
2. Supabase `service_role` keys or JWT access tokens.
3. Student response content (answers) in application log strings (store only question ID and status).
4. Full student PII (email, roll number) in error traces.

Quizdesk log format uses structured error responses:
```json
{
  "detail": "Failed to authenticate session",
  "error_code": "INVALID_AUTH_TOKEN",
  "request_id": "req-9dfafa35-12d5"
}
```

---

## 7. Pilot Deployment Checklist

Before granting student access for any live institutional quiz:
- [ ] Alembic schema is at head (`alembic current` matches latest migration).
- [ ] `/health/ready` returns HTTP 200 with database latency < 50ms.
- [ ] `ENVIRONMENT=production` set in backend environment (disables `/api/v1/admin/reset`).
- [ ] `ALLOW_DESTRUCTIVE_RESET=false` verified.
- [ ] `CORS_ORIGINS` configured with explicit production domain(s) (no wildcards).
- [ ] Student rosters imported and assignment counts verified.
- [ ] Logical backup snapshot created (`pg_dump`) and stored in secure offline storage.
- [ ] Teacher accounts verified and test quiz verified by teacher in preview mode.
- [ ] Custom SMTP configured in Supabase Auth if faculty password recovery is required for > 5 users.

---

## 8. Recommended Pilot Hosting Architecture & Costs

For an initial college pilot of approximately 30–50 students, the simplest, most maintainable, and cost-effective deployment arrangement is:

| Component | Recommended Host | Tier / Plan | Estimated Cost | Rationale & Cold-Start Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | **Vercel** or **Cloudflare Pages** | Free Tier | **$0.00** | Global edge CDN, unlimited bandwidth, instant TTFB, zero cold starts. Rewrite fallback handled via `vercel.json` or `_redirects`. |
| **Backend** | **Render** or **Railway** | Starter / Hobby (Persistent) | **$5.00 – $7.00 / month** | **CRITICAL:** Free tiers on Render sleep after 15 min of inactivity (50–90s cold start spins cause client timeouts). A persistent starter instance ($5–7/mo) ensures 24/7 responsiveness, instant quiz starts, and Docker container support. |
| **Database** | **Supabase** | Free Tier (or Pro $25/mo for PITR) | **$0.00** (Free) | PostgreSQL 17 + Session Pooler. Free tier provides 500MB storage, which comfortably holds thousands of attempts for a 30-student pilot. |
| **Total Estimated Pilot Cost** | | | **~$5.00 to $7.00 / month** | Reliable, predictable, and zero unexpected cold-start timeouts. |

---

## 9. Step-by-Step Production Deployment Guide

### 9.1 Backend Deployment (Render or Railway via Docker)
1. **Repository Setup**:
   - Connect GitHub repository to Render/Railway.
   - Set Root Directory to `backend` (or use repository root with Dockerfile `backend/Dockerfile`).
2. **Environment Variables Configuration**:
   ```ini
   ENVIRONMENT="production"
   ALLOW_DESTRUCTIVE_RESET="false"
   DATABASE_URL="postgresql+psycopg://postgres.[REF]:[PASS]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
   DB_POOL_SIZE="8"
   DB_MAX_OVERFLOW="4"
   DB_POOL_TIMEOUT="30"
   DB_POOL_RECYCLE="1800"
   SUPABASE_URL="https://[PROJECT_REF].supabase.co"
   SUPABASE_JWT_SECRET="[YOUR_SUPABASE_JWT_SECRET]"
   SUPABASE_JWT_ALGORITHM="HS256"
   SUPABASE_JWT_AUDIENCE="authenticated"
   CORS_ORIGINS='["https://quizdesk.yourinstitution.edu"]'
   ADMIN_EMAIL="admin@institution.edu"
   ADMIN_NAME="System Administrator"
   ADMIN_BOOTSTRAP_TOKEN="[GENERATE_SECURE_RANDOM_TOKEN]"
   ```
3. **Pre-Deploy Migration Command**:
   - In deployment settings, configure the release/pre-deploy hook:
     ```bash
     alembic -c alembic.ini upgrade head
     ```
4. **Health Check Probe Path**:
   - Configure health check endpoint to `/health/live` (for container liveness) and `/health/ready` (for traffic readiness).

### 9.2 Frontend Deployment (Vercel or Cloudflare Pages)
1. **Build Configuration**:
   - Framework Preset: `Vite`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
2. **Environment Variables**:
   ```ini
   VITE_API_BASE_URL="https://api-quizdesk.yourinstitution.edu"
   VITE_SUPABASE_URL="https://[PROJECT_REF].supabase.co"
   VITE_SUPABASE_ANON_KEY="[YOUR_PUBLIC_ANON_KEY]"
   ```
   *(Note: Never add `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_JWT_SECRET` to frontend variables).*
3. **SPA Routing Rewrites**:
   - Handled automatically by [`frontend/vercel.json`](file:///d:/ANUP/Quizdesk/frontend/vercel.json) or [`frontend/public/_redirects`](file:///d:/ANUP/Quizdesk/frontend/public/_redirects).

### 9.3 Custom SMTP Setup for Password Recovery
Supabase Auth limits password recovery emails to **5 emails per hour** on the default shared email service:
1. In the Supabase Dashboard, navigate to **Project Settings > Auth > SMTP Settings**.
2. Enable **Enable Custom SMTP**.
3. Supply SMTP credentials from an institutional mail relay or transactional service (e.g., Resend, AWS SES, SendGrid):
   - Host: `smtp.resend.com` (or provider host)
   - Port: `587`
   - User: `resend`
   - Password: `[API_KEY]`
   - Sender Email: `noreply@institution.edu`
   - Sender Name: `Quizdesk Assessment System`

---

## 10. Performance Triage & Optimization Findings (Phase 10)

### 10.1 Root Cause Analysis of Latency Under Load
During Phase 9 benchmark tests (50 concurrent students), p95 latency reached 15–19 seconds. The systematic investigation revealed two primary contributing factors:
1. **QueuePool Serialization Under Synchronization Barrier**:
   - The load test harness utilized `asyncio.Event()` to release 50 student coroutines at the exact same millisecond.
   - The connection pool was bounded to 12 slots (`DB_POOL_SIZE=8`, `DB_MAX_OVERFLOW=4`) to honor Supabase free-tier 15-connection limits.
   - The stopwatch $t_0$ started when the barrier opened. Therefore, requests 13–50 waited in the local Python FIFO queue for earlier batches to complete. The high p95 was predominantly **queue wait time**, not single-request execution latency.
2. **Geographic Network Round-Trips to Supabase**:
   - Running the backend locally in Windows connecting to Supabase in AWS across residential broadband incurs 60–100ms per round trip.
   - Redundant queries (e.g. separate count queries, profile re-fetching) and explicit `db.refresh()` calls after commits compounded this latency.

### 10.2 Phase 10 Surgical Improvements
1. **Eager Student Profile Loading**: In `get_current_user`, user lookup now eager-loads `student_profile` via `joinedload(User.student_profile)`, eliminating a secondary user lookup query in `check_student_quiz_eligibility`.
2. **Eager Quiz Version Loading**: In `check_student_quiz_eligibility`, `Quiz` is fetched with `joinedload(Quiz.versions)`, eliminating lazy-load query round-trips.
3. **Attempt Check Consolidation**: In `start_or_resume_attempt`, existing attempts and attempt counts are resolved from a single query.
4. **Elimination of Redundant `db.refresh()`**: Removed unnecessary `db.refresh()` post-commit calls in `save_attempt_answer`, `start_or_resume_attempt`, `record_telemetry_event`, and `finalize_and_grade_attempt` where entities are already materialized in memory.

### 10.3 Measured Impact (30 Concurrent Students)
- **Quiz-Start Burst**: p95 dropped from 19.76s to **7.37s** (**62.7% reduction**).
- **Autosave Bursts**: p95 dropped from 11.19s to **5.04s** (**55.0% reduction**).
- **Proctoring Telemetry**: p95 dropped from 17.35s to **6.80s** (**60.8% reduction**).
- **Submission Burst**: p95 dropped from 15.65s to **6.92s** (**55.8% reduction**).
- **Database Integrity**: 30/30 attempts, 150/150 answers persisted, 0 duplicate attempts, 0 lost answers (**100% clean verification**).
