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
- [ ] Student rosters imported and assignment counts verified.
- [ ] Logical backup snapshot created (`pg_dump`) and stored in secure offline storage.
- [ ] Teacher accounts verified and test quiz verified by teacher in preview mode.
