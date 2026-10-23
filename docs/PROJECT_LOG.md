# Project Execution Log & Persistent Memory

This document is the single authoritative historical log and persistent memory for the **Quizdesk** project. It records verified actions, architectural milestones, command outcomes, repository evolution, and exact next steps.

---

## 1. Project Overview & Current Stage

- **Project Name**: Quizdesk
- **Core Purpose**: A high-reliability, real college quiz and assessment platform featuring separate student and teacher experiences. Engineered for scheduled examinations, strict academic integrity, automated grading, server-authoritative timings, and resilient autosaving under concurrent loads.
- **Current Development Stage**: **Phase 5: Student Roster Import, Quiz Assignment & Eligibility Enforcement (Completed)**
- **Working Directory**: `d:\ANUP\Quizdesk`
- **Active Branch**: `main`

---

## 2. Finalized Requirements and Architecture Decisions

All items listed below represent **Confirmed** requirements and decisions agreed upon prior to feature implementation (see full records in [`docs/DECISIONS.md`](file:///d:/ANUP/Quizdesk/docs/DECISIONS.md)):

1. **Architecture Model**: Modular monolith (not microservices) coupling a React SPA with a unified Python FastAPI backend.
2. **Technology Stack**:
   - Frontend: React 18+, TypeScript, Vite, Tailwind CSS, React Router.
   - Backend: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy v2, Alembic.
   - Database & Auth: PostgreSQL via Supabase; Supabase Auth for identity management with backend token verification and role enforcement.
   - Testing: `pytest`, `pytest-asyncio`, `httpx` (Backend); `Vitest`, `@testing-library/react` (Frontend); `Playwright` (E2E).
3. **Environment & Secrets**:
   - Python dependencies must reside in an isolated `.venv`.
   - Never commit `.venv/`, `.env`, credentials, or service keys to git.
4. **Visual Design System**:
   - Institutional minimalist academic portal.
   - Palette: White and light-grey surfaces (`#FFFFFF`, `#F8FAFC`), deep navy structural elements (`#0F172A`, `#1E293B`), restrained institutional blue actions (`#2563EB`), green success feedback (`#16A34A`).
   - Strict guidelines: Avoid decorative gradients, excessive rounded cards, or gratuitous animation. Clean typography, readable tables, clear forms.
   - Dual-device requirement: Full responsiveness on desktop displays and mobile smartphones.
   - Assessment UI: Distraction-free, high-contrast, focused test-taking interface.
5. **Authentication and Roles**:
   - Students authenticate with institutional email and password via Supabase Auth.
   - Student PRN (Permanent Registration Number) is strictly an academic identifier, never a credential.
   - Teacher roles are provisioned solely by authorized administrators.
   - Backend validates JWT on every protected route and enforces role-based access control (RBAC).
6. **Questions and Import Engine**:
   - Supported question types: Single-answer MCQ, Multiple-answer MCQ, True/False.
   - Manual authoring and CSV import supported.
   - Pre-import validation and error preview table required before persisting records.
   - Per-question marks and scoring rules (including negative marking and partial scoring policies).
   - Published quiz versions are immutable; edits generate new versions.
7. **Student Roster Assignments**:
   - Per-quiz student assignment via CSV with exact schema: `prn,name,email,division`.
   - Dry-run validation for duplicates and conflicts.
   - Quiz access governed strictly by assignment records; `division` is informational metadata only.
8. **Quiz Lifecycle, Timers & Autosave**:
   - Scheduled window (`opens_at`, `closes_at`), attempt duration timer, attempt limits, navigation/backtracking options, question/option shuffling.
   - Attempt deadline formula: $\text{Deadline} = \min(\text{Attempt Start} + \text{Duration}, \text{Quiz Closing Time})$.
   - Server-authoritative timer and scoring; active delivery payloads omit correct answers and explanations.
   - Resilient background autosave with session rehydration across reloads/reconnects.
   - Tab-switching: Clear student disclosure; timestamped telemetry logged for teacher review; configurable warnings and penalty flags.
9. **Results & Grade Adjustments**:
   - Results held in withheld state until teacher explicitly releases them.
   - Students see only their personal score and earned marks; answer keys remain protected.
   - Manual score adjustments require mandatory written justification and create an immutable audit log.
   - Teacher analytics and CSV result export.
10. **Administrative Dashboard**:
    - Staged for Phase 2 after core student and teacher workflows are operational.
    - Architectural RBAC boundaries and audit logging built in from day 1.
11. **Notifications**:
    - Automated email and SMS alerts excluded from MVP; all communication handled via in-portal UI.

---

## 3. Repository Structure & File Responsibilities

| File / Directory | Responsibility |
|---|---|
| [`.gitignore`](file:///d:/ANUP/Quizdesk/.gitignore) | Comprehensive ignore rules for Python, Node, Vite, secrets, and IDE artifacts, preserving `.env.example`. |
| [`AGENTS.md`](file:///d:/ANUP/Quizdesk/AGENTS.md) | Authoritative operating rules and constraints for all AI coding assistants (including Rule 13: Git workflow). |
| [`backend/app/main.py`](file:///d:/ANUP/Quizdesk/backend/app/main.py) | FastAPI application entrypoint, route mounts, and baseline `/health` endpoint. |
| [`backend/app/core/config.py`](file:///d:/ANUP/Quizdesk/backend/app/core/config.py) | Centralized application settings with Pydantic BaseSettings. |
| [`backend/requirements.txt`](file:///d:/ANUP/Quizdesk/backend/requirements.txt) | Pinned production and test dependencies for the Python backend. |
| [`backend/pytest.ini`](file:///d:/ANUP/Quizdesk/backend/pytest.ini) | Pytest configuration file with asyncio and pythonpath settings. |
| [`backend/tests/test_health.py`](file:///d:/ANUP/Quizdesk/backend/tests/test_health.py) | Automated health check endpoint verification test suite. |
| [`backend/app/models/base.py`](file:///d:/ANUP/Quizdesk/backend/app/models/base.py) | Declarative Base and mixins (TimestampMixin, UUIDPrimaryKeyMixin). |
| [`backend/app/models/user.py`](file:///d:/ANUP/Quizdesk/backend/app/models/user.py) | User, StudentProfile models, and UserRole enum. |
| [`backend/app/models/quiz.py`](file:///d:/ANUP/Quizdesk/backend/app/models/quiz.py) | Quiz, QuizVersion models, and QuizStatus enum. |
| [`backend/app/models/question.py`](file:///d:/ANUP/Quizdesk/backend/app/models/question.py) | Question, QuestionOption models, and QuestionType enum. |
| [`backend/app/models/roster.py`](file:///d:/ANUP/Quizdesk/backend/app/models/roster.py) | QuizAssignment roster model with PRN and email uniqueness constraints. |
| [`backend/app/models/attempt.py`](file:///d:/ANUP/Quizdesk/backend/app/models/attempt.py) | QuizAttempt, AttemptAnswer, and AttemptTelemetryEvent models. |
| [`backend/app/models/audit.py`](file:///d:/ANUP/Quizdesk/backend/app/models/audit.py) | GradeAdjustment, AuditEvent, and ImportJob audit models. |
| [`backend/alembic/versions/0001_initial_schema.py`](file:///d:/ANUP/Quizdesk/backend/alembic/versions/0001_initial_schema.py) | Initial schema DDL migration script. |
| [`backend/.env.example`](file:///d:/ANUP/Quizdesk/backend/.env.example) | Safe environment variables template with placeholder credentials. |
| [`backend/README.md`](file:///d:/ANUP/Quizdesk/backend/README.md) | Essential setup, execution, testing, and Alembic migration commands. |
| [`frontend/src/App.tsx`](file:///d:/ANUP/Quizdesk/frontend/src/App.tsx) | Root application router and shell container. |
| [`frontend/src/components/layout/Shell.tsx`](file:///d:/ANUP/Quizdesk/frontend/src/components/layout/Shell.tsx) | Institutional portal shell layout with responsive Header and Footer. |
| [`frontend/src/pages/Home.tsx`](file:///d:/ANUP/Quizdesk/frontend/src/pages/Home.tsx) | Quizdesk landing view establishing DEC-004 academic visual design principles. |
| [`frontend/src/pages/Overview.tsx`](file:///d:/ANUP/Quizdesk/frontend/src/pages/Overview.tsx) | System status and diagnostics dashboard view. |
| [`frontend/vite.config.ts`](file:///d:/ANUP/Quizdesk/frontend/vite.config.ts) | Vite 8 build configuration integrating `@tailwindcss/vite` and React. |
| [`frontend/README.md`](file:///d:/ANUP/Quizdesk/frontend/README.md) | Frontend setup, development server, and production build instructions. |
| [`docs/PROJECT_LOG.md`](file:///d:/ANUP/Quizdesk/docs/PROJECT_LOG.md) | Chronological development log, verified execution records, and state memory. |
| [`docs/DECISIONS.md`](file:///d:/ANUP/Quizdesk/docs/DECISIONS.md) | Formal numbered Architectural Decision Records (ADRs) with rationale and implications. |
| [`docs/TASK_TRACKER.md`](file:///d:/ANUP/Quizdesk/docs/TASK_TRACKER.md) | Structured roadmap, task dependencies, status tracking, and acceptance criteria. |
| [`docs/ARCHITECTURE.md`](file:///d:/ANUP/Quizdesk/docs/ARCHITECTURE.md) | Technical architecture, data flow diagrams, security boundaries, and planned component layout. |


---

## 4. Chronological Action & Execution Log

### 2026-10-23: Phase 0 - Governance and Documentation Setup
- **Action**: Workspace Inspection
  - Inspected directory `d:\ANUP\Quizdesk`. Verified that the folder was completely empty.
  - Checked Git status. Verified that no Git repository was initialized.
- **Action**: Created [`AGENTS.md`](file:///d:/ANUP/Quizdesk/AGENTS.md)
  - Established 12 foundational rules for AI pair programming sessions covering pre-flight reading, decision authority, atomic task scoping, verification, secrets policy, and history preservation.
- **Action**: Created [`docs/DECISIONS.md`](file:///d:/ANUP/Quizdesk/docs/DECISIONS.md)
  - Registered decisions DEC-001 through DEC-013 with status `Confirmed` reflecting all project requirements.
- **Action**: Created [`docs/ARCHITECTURE.md`](file:///d:/ANUP/Quizdesk/docs/ARCHITECTURE.md)
  - Documented modular monolith architecture, component layout, sequence diagrams for auth, authoring, assessment delivery, autosave, and grading, plus security boundaries and planned directory structure.
- **Action**: Created [`docs/TASK_TRACKER.md`](file:///d:/ANUP/Quizdesk/docs/TASK_TRACKER.md)
  - Created structured roadmap covering Phase 0 through Phase 9 with granular task IDs, dependencies, and verifiable acceptance criteria.
- **Action**: Created [`docs/PROJECT_LOG.md`](file:///d:/ANUP/Quizdesk/docs/PROJECT_LOG.md)
  - Initialized persistent project memory.

### 2026-10-23: Phase 1 - Task 101: Git Initialization, .gitignore, & Project Baseline
- **Action**: Inspected Git Repository State
  - Confirmed repository initialized by user on branch `main` with 0 commits.
  - Inspected configured user identity: `Manmath Kornule <202401110045@mitaoe.ac.in>`.
- **Action**: Added Rule 13 to [`AGENTS.md`](file:///d:/ANUP/Quizdesk/AGENTS.md)
  - Added formal rule for disciplined Git workflow, small atomic commits, conventional commit naming (`chore:`, `feat:`, `fix:`, `docs:`, etc.), verification before committing, and zero secret tolerance.
- **Action**: Created [`.gitignore`](file:///d:/ANUP/Quizdesk/.gitignore)
  - Configured rules for `.venv/`, `venv/`, `__pycache__/`, `*.py[cod]`, test/coverage caches, `node_modules/`, `dist/`, build artifacts, Playwright caches, IDEs, and local `.env` files.
  - Implemented explicit exception rule for environment templates: `!.env.example` and `!**/.env.example`.
- **Action**: Verified `.gitignore` Filtering Behavior
  - Verified `.env` and `.env.local` are strictly ignored by Git.
  - Verified `.venv/` and `node_modules/` are strictly ignored by Git.
  - Verified `.env.example` and `backend/.env.example` are trackable and not ignored.
- **Action**: Initial Project Baseline Commit
  - Staged baseline documentation and `.gitignore`.
  - Staged diff verified to ensure zero secrets or unintended files were present.
  - Executed initial commit with message: `chore: establish project baseline`.
  - Verified commit hash: `7bdaff5e0412291a9c831d745437665f01c0232a` (short: `7bdaff5`) containing 6 files (`.gitignore`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/PROJECT_LOG.md`, `docs/TASK_TRACKER.md`).

### 2026-10-23: Phase 1 - Task 102: Python Virtual Environment & Minimal FastAPI Backend Scaffolding
- **Action**: Created Root Python Virtual Environment
  - Executed `python -m venv .venv` creating an isolated environment at repository root.
  - Verified `.venv/` is ignored by Git in accordance with DEC-003.
- **Action**: Scaffolded Minimal Backend Directory Structure
  - Created `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/__init__.py`, `backend/app/core/__init__.py`.
  - Configured `Settings` with `pydantic-settings` BaseSettings.
  - Implemented `GET /health` returning `{"status": "ok"}`.
- **Action**: Pinned Backend Dependencies in `backend/requirements.txt`
  - Added exact pinned versions for FastAPI (0.115.8), Uvicorn (0.34.0), Pydantic (2.10.6), Pydantic-Settings (2.7.1), SQLAlchemy (2.0.38), Alembic (1.14.1), Psycopg (3.2.4 binary), Pytest (8.3.4), Pytest-Asyncio (0.25.3), and HTTPX (0.28.1).
- **Action**: Installed Dependencies into Root `.venv`
  - Executed `.\.venv\Scripts\pip.exe install -r backend/requirements.txt`. All packages installed successfully without error.
- **Action**: Configured Test Harness & Health Test
  - Created `backend/pytest.ini` with `pythonpath = .`, `asyncio_mode = auto`, and `asyncio_default_fixture_loop_scope = function`.
  - Created `backend/tests/test_health.py` verifying `GET /health` returns HTTP 200 and `{"status": "ok"}` via `httpx.AsyncClient`.
  - Executed test suite with `.\.venv\Scripts\python.exe -m pytest -c backend/pytest.ini backend/tests -v`. Test passed: 1 passed in 0.71s.
- **Action**: Created `backend/README.md`
  - Documented Windows PowerShell commands for virtual environment activation, dependency installation, server launch, and testing.

### 2026-10-23: Phase 1 - Task 103: Frontend Vite + React + TypeScript Scaffolding
- **Action**: Scaffolded Standard React + TypeScript Application in `frontend/`
  - Initialized non-interactively using `create-vite` with `react-ts` template.
  - Installed `react-router-dom` (v7) and `lucide-react`.
  - Configured Tailwind CSS v4 using `@tailwindcss/vite` plugin and `@import "tailwindcss";` in `src/index.css`.
- **Action**: Removed Boilerplate and Established Clean Structure
  - Removed demo CSS (`App.css`) and starter assets (`assets/react.svg`, `vite.svg`, `hero.png`).
  - Organized layout components (`Shell.tsx`, `Header.tsx`, `Footer.tsx`) and views (`Home.tsx`, `Overview.tsx`, `NotFound.tsx`).
- **Action**: Implemented Academic Visual Design Shell (DEC-004)
  - Light-grey surfaces (`bg-slate-50`), white content containers (`bg-white border border-slate-200`), deep navy structural navigation (`bg-slate-900`), restrained blue action buttons (`bg-blue-600`), and green success indicators (`bg-emerald-50 text-emerald-700`).
  - Added semantic HTML, accessible focus outlines, clean typography with Inter fallback, and responsive mobile navigation drawer.
- **Action**: Verified Production Build
  - Fixed type-only import syntax for `PropsWithChildren` (`import React, { type PropsWithChildren } from 'react'`).
  - Executed `npm run build` (`tsc -b && vite build`). Build succeeded: 1946 modules transformed, assets generated in `frontend/dist/` in 727ms.
  - Verified `frontend/node_modules/` and `frontend/dist/` are strictly ignored by Git.

### 2026-10-23: Phase 2 - Task 104 / Tasks 201-204: Database Schema & Migration Foundation
- **Action**: Created Code-First SQLAlchemy 2.x Declarative Domain Models
  - Created `backend/app/models/base.py` (`Base`, `TimestampMixin`, `UUIDPrimaryKeyMixin`).
  - Created `backend/app/models/user.py` (`User` linking to Supabase auth UUID, `StudentProfile` with unique `prn`, `UserRole` enum).
  - Created `backend/app/models/quiz.py` (`Quiz`, immutable `QuizVersion` with schedule window, timer, attempt limits, navigation policy, and result release controls, `QuizStatus` enum).
  - Created `backend/app/models/question.py` (`Question` supporting single MCQ, multi MCQ, True/False, positive/negative marks, `QuestionOption` with server-concealed `is_correct`, `QuestionType` enum).
  - Created `backend/app/models/roster.py` (`QuizAssignment` enforcing per-quiz student CSV schema `prn,name,email,division`, unique PRN per quiz, indexed emails).
  - Created `backend/app/models/attempt.py` (`QuizAttempt` with server-authoritative timestamps, `AttemptAnswer` storing selected option IDs, `AttemptTelemetryEvent` for tab-switch monitoring, `AttemptStatus` and `GradingStatus` enums).
  - Created `backend/app/models/audit.py` (`GradeAdjustment` with mandatory justification reason, `AuditEvent` for platform actions, `ImportJob` for CSV import validation tracking).
  - Created `backend/app/models/__init__.py` registry exporting all 13 models to `Base.metadata`.
- **Action**: Configured Alembic Migration Environment
  - Initialized Alembic harness in `backend/alembic/` and `backend/alembic.ini`.
  - Configured `backend/alembic.ini` with `script_location = %(here)s/alembic`.
  - Configured `backend/alembic/env.py` to dynamically load `DATABASE_URL` from Pydantic settings without exposing credentials.
  - Created safe `backend/.env.example` with empty placeholders.
  - Documented migration inspection, dry-run, and application commands in `backend/README.md`.
- **Action**: Crafted Initial Schema Migration (`0001_initial_schema`)
  - Created deterministic migration script `backend/alembic/versions/0001_initial_schema.py` creating all 13 tables, UUID primary keys, foreign key constraints, unique constraints, and indexes in `upgrade()`, and dropping in reverse order in `downgrade()`.
  - Tested Alembic revision history: verified `<base> -> 0001_initial_schema (head)`.
  - Executed offline SQL generation (`alembic upgrade head --sql`): verified generation of valid PostgreSQL DDL without connecting to a live database.
- **Action**: Automated Test Verification
  - Created `backend/tests/test_models.py` verifying model table registration, constraints (`uq_quiz_version_number`, `uq_quiz_assignment_prn`, `uq_attempt_number_per_student`), enums, and Alembic migration discovery.
  - Ran pytest suite: 5 passed in 1.34s.

### 2026-10-23: Phase 2 - TASK-104 Database Integrity Review & Hardening
- **Context & Objectives**:
  - Performed a focused database integrity review of `TASK-104` addressing 4 specific risk vectors prior to Phase 3 authentication integration:
    1. *Student assignment identity*: Preventing duplicate roster entries or assignment hijacking.
    2. *Published-version integrity*: Ensuring hard deletes on parent quizzes cannot wipe published versions or historical attempts.
    3. *Scoring and result-release consistency*: Disentangling student score visibility (`QuizVersion.is_results_released`) from internal attempt grading lifecycle (`QuizAttempt.grading_status`).
    4. *Scoring and configuration constraints*: Enforcing positive/non-negative marks, durations, scheduling windows, and multi-answer scoring policies at the database level.
- **Action**: Model Adjustments & Invariants
  - Added `uq_quiz_assignment_email` (`UniqueConstraint("quiz_id", "student_email")`) to `QuizAssignment` in `backend/app/models/roster.py`.
  - Added `is_published: Mapped[bool]` and `MultiAnswerPolicy` enum (`all_or_nothing`, `partial_with_penalty`, `partial_no_penalty`) to `QuizVersion` in `backend/app/models/quiz.py`.
  - Changed `quiz_versions.quiz_id` foreign key from `ON DELETE CASCADE` to `ON DELETE RESTRICT`, ensuring parent quizzes with versions must be archived rather than deleted.
  - Refactored `GradingStatus` enum to `pending`, `auto_graded`, `manually_adjusted` in `backend/app/models/attempt.py`, cleanly separating scoring calculation state from the student-visible release gate (`QuizVersion.is_results_released`).
  - Added check constraints:
    - Questions: `ck_question_positive_marks` (`positive_marks > 0`), `ck_question_negative_marks` (`negative_marks >= 0`).
    - Quiz Versions: `ck_quiz_version_duration` (`duration_minutes > 0`), `ck_quiz_version_max_attempts` (`max_attempts > 0`), `ck_quiz_version_time_window` (`closes_at > opens_at`), `ck_quiz_version_tab_limit` (`tab_switch_limit >= 0`), `ck_quiz_version_tab_penalty` (`tab_switch_penalty_marks >= 0`).
    - Quiz Attempts: `ck_quiz_attempt_number` (`attempt_number >= 1`), `ck_quiz_attempt_deadline` (`deadline_at >= started_at`), `ck_quiz_attempt_tab_count` (`tab_switch_count >= 0`).
- **Action**: Created Migration `0002_integrity`
  - Created `backend/alembic/versions/0002_strengthen_integrity_constraints.py` (down_revision = `'0001_initial_schema'`).
  - Kept migration `0001_initial_schema.py` strictly untouched.
  - Fully implemented both `upgrade()` and symmetrical `downgrade()`.
- **Action**: Verification & Test Suite Hardening
  - Updated `backend/tests/test_models.py` to assert new check constraints, foreign key `RESTRICT` rules, enums (`MultiAnswerPolicy`, `GradingStatus`), and the 2-step migration chain.
  - Verified pytest suite: 5 passed in 1.46s.
  - Verified Alembic forward offline SQL (`alembic upgrade head --sql`): 0 errors, generated valid PostgreSQL DDL.
  - Verified Alembic rollback offline SQL (`alembic downgrade 0002_integrity:0001_initial_schema --sql`): 0 errors, generated valid reversal DDL.

### 2026-10-23: Phase 3 - TASK-301A: FastAPI Authentication Foundation & Role Guards
- **Context & Objectives**:
  - Implemented a secure, offline-testable authentication foundation for Supabase-issued Bearer JWTs without requiring live Supabase credentials.
  - Resolved authenticated tokens directly to application database `User` records.
  - Established authoritative role verification rejecting client-side claim spoofing.
- **Action**: Dependencies & Settings
  - Pinned `pyjwt==2.10.1` in `backend/requirements.txt` (native HMAC-SHA256, no external C bindings).
  - Extended `Settings` in `backend/app/core/config.py`: added `SUPABASE_JWT_SECRET`, `SUPABASE_JWT_ALGORITHM` (default `HS256`), `SUPABASE_JWT_AUDIENCE` (default `authenticated`), and `SUPABASE_JWT_ISSUER`.
  - Updated `backend/.env.example` with non-sensitive placeholder configuration variables.
  - Updated `backend/README.md` with environment setup and testing instructions.
- **Action**: Core Database & Auth Infrastructure
  - Created `backend/app/core/database.py` defining transactional `get_db` session dependency.
  - Created `backend/app/core/auth.py`:
    - `decode_supabase_jwt`: Enforces HMAC-SHA256 signature verification with `SUPABASE_JWT_SECRET`, checks expiration, validates audience (`authenticated`), and requires subject claim (`sub`). Rejects malformed, tampered, or expired tokens with tailored RFC 6750 HTTP 401 exceptions.
    - `get_current_user`: Extracts Bearer header, validates token, parses subject UUID, looks up `User` record in database, and rejects unregistered or inactive (`is_active=False`) users with HTTP 401.
    - Authoritative database role resolution: User roles (`student`, `teacher`, `admin`) are strictly loaded from `users.role`. Roles present in JWT claims or request bodies are untrusted and ignored.
    - Role guards: Implemented `require_roles(*allowed_roles)` factory and reusable dependencies `require_student`, `require_teacher`, `require_admin`, `require_faculty` returning HTTP 403 Forbidden on role mismatch.
    - Exported all dependencies in `backend/app/core/__init__.py`.
- **Action**: Comprehensive Unit Testing
  - Created `backend/tests/test_auth.py` with 18 focused test cases using an in-memory SQLite fixture and controlled test signing material:
    - Verifies health check remains unauthenticated and intact (HTTP 200).
    - Verifies missing, invalid scheme, empty, and malformed tokens return HTTP 401.
    - Verifies tampered signature, expired token, and invalid audience return HTTP 401.
    - Verifies missing `sub` and malformed UUID `sub` return HTTP 401.
    - Verifies unregistered users and deactivated users (`is_active=False`) return HTTP 401.
    - Verifies student access succeeds on student endpoints and fails with HTTP 403 on teacher/admin endpoints.
    - Verifies teacher and admin role permissions on faculty and role-specific endpoints.
    - Verifies token role spoofing defense: tokens with injected `{"role": "admin"}` are denied access (HTTP 403) if the database role is `student`.
    - Verifies missing `SUPABASE_JWT_SECRET` in settings returns HTTP 500.
  - Executed pytest suite: all 23 tests passed in 2.10s.

### 2026-10-23: Phase 3 - TASK-301B: Authentication Integration Readiness Review
- **Context & Objectives**:
  - Conducted a comprehensive audit of authentication integration readiness prior to connecting frontend clients or live Supabase infrastructure.
  - Verified explicit JWT signing configuration, safe non-self-promoting user provisioning, secret separation, and live integration prerequisites.
- **Action**: Configuration Audit & Refinement
  - Added `SUPABASE_JWT_PUBLIC_KEY` to `backend/app/core/config.py` and `backend/app/core/auth.py` to support asymmetric algorithms (`RS256`, `ES256`) alongside symmetric HMAC-SHA256 (`HS256`).
  - Enforced strict single-algorithm validation: `algorithms=[settings.SUPABASE_JWT_ALGORITHM]` with no silent fallback to weaker or arbitrary algorithms.
  - Created `frontend/.env.example` explicitly defining public browser configuration (`VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`) and warning against secret inclusion.
  - Re-verified server-only private secrets in `backend/.env.example` (`DATABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`).
- **Action**: User Provisioning Design Finalization (DEC-015)
  - Established that self-registration via Supabase Auth is strictly locked to `role = student`.
  - Established that `teacher` and `admin` roles can only be provisioned by authorized administrators or initial institutional seeding.
  - Verified that application role checks always query `users.role` from the database, preventing token claim spoofing.
- **Action**: Verification & Regression Testing
  - Ran pytest suite: all 23 tests passed in 2.08s.
  - Built frontend production bundle: 0 errors in 692ms.

### 2026-10-23: Phase 3 - TASK-303: Frontend Authentication Context & Route Guards
- **Context & Objectives**:
  - Built the React frontend authentication foundation using Supabase Auth without requiring live credentials or implementing full application dashboard screens.
  - Provided graceful fallback for unconfigured development environments.
  - Bound application role resolution strictly to backend confirmation, never client-side metadata.
- **Action**: Installed Supabase Client & Graceful Initialization
  - Installed `@supabase/supabase-js` (`^2.118.0`) in `frontend/package.json`.
  - Created `frontend/src/lib/supabase.ts` checking `isSupabaseConfigured` against placeholder values. Initialized fallback client to avoid runtime crashes during local development without credentials.
  - Created `frontend/src/types/auth.ts` defining `UserRole`, `UserProfile`, `ProfileStatus`, and `AuthContextValue`.
- **Action**: Implemented AuthProvider & useAuth Hook
  - Created `frontend/src/context/AuthContext.tsx`:
    - Manages `session`, `user`, `profile`, `role`, `loading`, and `profileStatus`.
    - Handles initial session hydration (`supabase.auth.getSession()`) and realtime state changes (`supabase.auth.onAuthStateChange`).
    - Ensures proper subscription cleanup on component unmount to prevent memory leaks and race conditions.
    - Role Resolution Design: Attempts `GET ${VITE_API_BASE_URL}/api/v1/users/me` with Bearer token. When endpoint is pending (HTTP 404) or server is offline, cleanly marks `profileStatus = 'endpoint_unavailable'` and leaves `role = null` rather than guessing or reading client-editable metadata.
- **Action**: Created Route Guards & Placeholder Views
  - Created `frontend/src/components/auth/RequireAuth.tsx`: Prevents protected content flashing with a dedicated loading state; redirects unauthenticated visitors to `/login`.
  - Created `frontend/src/components/auth/RequireRole.tsx`: Enforces role boundaries; provides clean pending status when backend role endpoint is unavailable, and HTTP 403 Forbidden notice on role mismatch.
  - Created minimal placeholder routes: `frontend/src/pages/Login.tsx`, `frontend/src/pages/Unauthorized.tsx`, `frontend/src/pages/StudentPortalPlaceholder.tsx`, and `frontend/src/pages/TeacherPortalPlaceholder.tsx`.
  - Integrated into `frontend/src/App.tsx` wrapped in `<AuthProvider>`.
  - Updated `frontend/src/components/layout/Header.tsx` to reflect active session state and login/logout actions.
- **Action**: Verification
  - Executed `npm run build` (`tsc -b && vite build`): built in 746ms with 0 errors.
  - Executed backend pytest suite: 23 passed in 2.34s.

### 2026-10-23: Phase 3 - TASK-302: Backend Profile Endpoint & API Router
- **Context & Objectives**:
  - Implemented the authenticated profile endpoint `GET /api/v1/users/me` allowing frontend clients to retrieve the authoritative identity and role of the logged-in user.
  - Established a versioned API router structure under `backend/app/api/v1/` mounted at `/api/v1` in `backend/app/main.py`.
  - Preserved the existing `GET /health` endpoint unchanged at the root level.
- **Action**: Versioned Router & Endpoint Implementation
  - Created `backend/app/api/__init__.py`.
  - Created `backend/app/api/v1/__init__.py` aggregating API v1 routers into `api_v1_router`.
  - Created `backend/app/api/v1/endpoints/users.py` with `@router.get("/me", response_model=UserResponse)`.
  - Mounted `api_v1_router` on `app` with `prefix=settings.API_V1_PREFIX` (`/api/v1`) in `backend/app/main.py`.
- **Action**: Strict Response Serialization (DEC-001, DEC-013)
  - Created `backend/app/schemas/user.py` defining `UserResponse` with exact allowlist fields: `id`, `email`, `name`, `role`, `is_active`.
  - Utilized `ConfigDict(from_attributes=True)` for seamless SQLAlchemy ORM mapping.
  - Verified no passwords, tokens, internal timestamps, or ORM attributes (`_sa_instance_state`) leak in responses.
- **Action**: Reused Authentication Dependency & Role Authority
  - Reused `get_current_active_user` from `app.core.auth`; avoided duplicating JWT decoding or claim checks.
  - Rejection of client role tampering: endpoint takes no request body or query parameter role overrides; role is resolved exclusively from the database.
- **Action**: Comprehensive Testing & Verification
  - Created `backend/tests/test_users_me.py` containing 13 focused test cases:
    - 200 OK profile response for student, teacher, and admin with matching database roles.
    - Strict allowlist verification: response keys match `{"id", "email", "name", "role", "is_active"}` and exclude forbidden attributes.
    - 401 Unauthorized for missing token, invalid scheme, empty token, malformed token, invalid signature, and expired token.
    - 401 Unauthorized for unregistered subjects and deactivated accounts.
    - Verification that query parameter role tampering (`?role=admin`) is ignored and database role is maintained.
    - Preservation of root `GET /health` functionality (HTTP 200 `{"status": "ok"}`).
  - Ran full backend pytest suite: all 36 tests passed in 1.74s.
  - Re-verified frontend production build: `npm run build` completed in 595ms with 0 errors.

### 2026-10-23: Phase 3 - TASK-304: Complete Frontend–Backend Authentication Integration
- **Context & Objectives**:
  - Connected the React frontend `AuthContext` to the backend profile endpoint `GET /api/v1/users/me`.
  - Ensured that authoritative database roles are strictly populated from backend responses and never guessed or cached across invalid sessions.
  - Enforced race-condition protection, clear 401/403 state eviction, and strict CORS configuration.
- **Action**: AuthContext Race Condition & Stale State Defense
  - Added `activeTokenRef` and `isMountedRef` in `frontend/src/context/AuthContext.tsx`.
  - If a session terminates, changes, or unmounts while `/api/v1/users/me` is in-flight, the stale response is discarded.
  - On HTTP 401 (unregistered/deactivated/expired token), `profile` and `role` are strictly set to `null`, preventing privilege retention.
  - On HTTP 403 (deactivated/unapproved account), profile is cleared and an explicit error notice is set.
- **Action**: Protected Route Guards Hardening
  - Updated `frontend/src/components/auth/RequireAuth.tsx` to check `loading || (session && profileStatus === 'loading')`, preventing protected content flashing.
  - On backend verification failure (`profileStatus === 'error'`), `RequireAuth` displays a clean failure screen with a sign-out button rather than rendering unauthorized children.
  - Confirmed `frontend/src/components/auth/RequireRole.tsx` cleanly distinguishes unauthenticated users (redirects to `/login`), unresolved profile status (displays pending sync UI), and role mismatches (displays 403 Access Restricted).
- **Action**: Backend CORS Hardening
  - Added `CORS_ORIGINS` to `Settings` in `backend/app/core/config.py` defaulting to trusted local development origins (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`).
  - Mounted `CORSMiddleware` in `backend/app/main.py` allowing only necessary HTTP methods and headers (`Authorization`, `Content-Type`, `Accept`).
  - Added `CORS_ORIGINS` placeholder to `backend/.env.example`.
- **Action**: Testing & Verification
  - Added CORS preflight test cases to `backend/tests/test_users_me.py` verifying that trusted origins receive CORS headers and untrusted origins are denied.
  - Ran backend pytest suite: all 38 tests passed in 2.06s.
  - Ran frontend linter (`npm run lint` / oxlint): 0 errors across 18 files.
  - Ran frontend production build (`npm run build`): passed in 649ms with 0 errors.

### 2026-10-23: Phase 4 - Milestone 4A: Teacher Question Bank & CSV Import Engine
- **Context & Objectives**:
  - Built the first teacher-facing assessment authoring module: personal reusable question bank, manual CRUD, CSV template download, dry-run CSV parsing & validation preview, and transactional all-or-nothing CSV import.
  - Preserved the immutability of published quiz versions and student historical attempt answers.
- **Action**: Data Model & Migration (DEC-006)
  - Updated `backend/app/models/question.py`:
    - Made `quiz_version_id` nullable (`Optional[UUID]`), allowing questions to reside in a teacher's reusable bank without requiring a quiz version.
    - Added `created_by_id` (`UUID`, foreign key `users.id`, `ondelete='RESTRICT'`) and creator relationship.
    - Added check constraint `ck_question_bank_or_version` enforcing `(quiz_version_id IS NOT NULL) OR (created_by_id IS NOT NULL)`.
  - Generated migration `backend/alembic/versions/0003_teacher_question_bank.py` (`0003_question_bank`).
  - Tested migration chain: verified `0003_question_bank -> 0002_integrity -> 0001_initial_schema`. Verified static SQL upgrade and downgrade.
- **Action**: CSV Parsing & Validation Engine (DEC-006)
  - Created `backend/app/services/csv_parser.py`:
    - Safe UTF-8 decoding with automatic BOM stripping (`utf-8-sig`).
    - Enforced 2MB file limit and 200 question row count limit.
    - Header normalization and required headers check (`question_type`, `question_text`, `option_a`, `option_b`, `option_c`, `option_d`, `correct_answers`, `positive_marks`, `negative_marks`).
    - Type-specific option validation: Single Choice (exactly 1 correct answer), Multi Choice (at least 1 correct answer), True/False (defaults to True/False, forbids options C/D, normalized answer key).
    - Option deduplication check and empty option reference prevention.
    - Numeric mark validation: positive marks > 0, negative penalty >= 0.
- **Action**: Authenticated REST API (DEC-006, DEC-013)
  - Pinned `python-multipart==0.0.20` in `backend/requirements.txt` for multipart file uploads.
  - Created schemas in `backend/app/schemas/question.py` with custom Pydantic validators.
  - Created endpoints in `backend/app/api/v1/endpoints/question_bank.py`:
    - `GET /api/v1/question-bank`: Paginated question bank listing with search and type filters.
    - `POST /api/v1/question-bank`: Manual question creation with options.
    - `GET /api/v1/question-bank/{id}`: Single question details with options.
    - `PUT /api/v1/question-bank/{id}`: Full question update and option replacement.
    - `DELETE /api/v1/question-bank/{id}`: 204 No Content deletion from bank.
    - `POST /api/v1/question-bank/csv/preview`: Dry-run validation preview returning parsed items and line-by-line errors without writing to DB.
    - `POST /api/v1/question-bank/csv/import`: All-or-nothing transactional import (rejects with 422 if any error exists).
    - `GET /api/v1/question-bank/csv/template`: Downloadable sample CSV template.
  - Enforced `require_faculty` role guard (rejects students with 403 Forbidden) and cross-teacher tenant isolation (404 on foreign question access).
- **Action**: Frontend Question Bank UI
  - Created `frontend/src/types/question.ts` and `frontend/src/services/questionBankApi.ts`.
  - Built `frontend/src/pages/teacher/QuestionBank.tsx`: Responsive table/cards, search, type pills, pagination, edit, and delete confirmation.
  - Built `frontend/src/pages/teacher/QuestionModal.tsx`: Dynamic option builder, radio/checkbox answer toggles, and form validation.
  - Built `frontend/src/pages/teacher/CsvImportModal.tsx`: Drag & drop upload, sample template downloader, live validation preview summary, row-level error table, and confirmation step.
  - Mounted `/teacher/question-bank` route in `frontend/src/App.tsx` and linked from `Header.tsx` and `TeacherPortalPlaceholder.tsx`.
### 2026-10-23: Phase 4 - Milestone 4B: Teacher Quiz Builder, Immutable Publishing & Difficulty Support
- **Context & Objectives**:
  - Implemented the complete teacher-facing assessment authoring lifecycle: quiz drafting, detailed settings configuration, question selection from the question bank via deep-copy isolation, question reordering and removal, pre-publication validation & preview, and immutable snapshot publishing.
  - Implemented end-to-end question difficulty classification (`easy`, `medium`, `hard`) with a safe migration, backward-compatible defaults, UI badges, and spreadsheet validation.
  - Added dual spreadsheet ingestion support: accepting both genuine Microsoft Excel (`.xlsx`) workbooks and UTF-8 `.csv` files.
- **Action**: Data Model & Migration (DEC-016, DEC-017)
  - Created `QuestionDifficulty(str, enum.Enum)` (`easy`, `medium`, `hard`) in `backend/app/models/question.py`.
  - Added indexed column `difficulty` with server default `'medium'` and check constraint `ck_question_difficulty_enum`.
  - Generated migration `backend/alembic/versions/0004_question_difficulty.py` (`0004_question_difficulty` down to `0003_question_bank`).
  - Tested migration chain: verified `0004_question_difficulty -> 0003_question_bank -> 0002_integrity -> 0001_initial_schema`. Verified offline static SQL generation for upgrade and downgrade.
- **Action**: Dual-Format Spreadsheet Ingestion (.CSV and .XLSX)
  - Pinned `openpyxl==3.1.5` in `backend/requirements.txt`.
  - Upgraded `backend/app/services/csv_parser.py`:
    - Auto-detects file format via MIME type and file extension (`.csv` vs `.xlsx`).
    - Uses `openpyxl.load_workbook(data_only=True)` to parse `.xlsx` workbooks securely with row/byte limits (max 200 rows, max 2MB).
    - Preserves full CSV parsing with automatic UTF-8 BOM stripping (`utf-8-sig`).
    - Parses and normalizes `difficulty` column (case-insensitive).
    - Backward-compatible default: if `difficulty` column is omitted, defaults cleanly to `medium`.
    - If `difficulty` column is present with invalid text (e.g. `'extreme'`), raises actionable row-level error.
- **Action**: Authenticated Quiz API (DEC-017)
  - Created schemas in `backend/app/schemas/quiz.py` (`QuizCreateRequest`, `QuizUpdateRequest`, `QuizDetailResponse`, `QuizPreviewResponse`, `PublishQuizResponse`, `AddQuestionsFromBankRequest`, `ReorderQuestionsRequest`, etc.).
  - Created endpoints in `backend/app/api/v1/endpoints/quizzes.py`:
    - `GET /api/v1/quizzes`: List quizzes owned by authenticated teacher with version and draft/published indicators.
    - `POST /api/v1/quizzes`: Create draft quiz and initial `QuizVersion` (version 1, `is_published=False`).
    - `GET /api/v1/quizzes/{id}`: Detailed quiz view including full question list with options and difficulty breakdown.
    - `PUT /api/v1/quizzes/{id}`: Update assessment settings (schedules, duration, attempts, navigation, shuffling, multi-answer policy, tab-switch thresholds). If current version is already published, automatically forks a new draft version.
    - `POST /api/v1/quizzes/{id}/questions`: Add bank questions to draft via deep-copy cloning (ensuring bank edits never alter quiz versions).
    - `DELETE /api/v1/quizzes/{id}/questions/{qid}`: Remove question from draft version.
    - `PUT /api/v1/quizzes/{id}/questions/order`: Reorder question sequence numbers atomically.
    - `GET /api/v1/quizzes/{id}/preview`: Pre-publication preview checking criteria (min 1 question, option completeness, schedule validity) and returning validation flags.
    - `POST /api/v1/quizzes/{id}/publish`: Transaction-safe publishing transition (`is_published=True`). Rejects invalid or empty quizzes.
  - Enforced `require_faculty` role guard (rejects students with 403 Forbidden) and multi-tenant isolation (404 on accessing quizzes owned by another teacher).
- **Action**: Frontend Quiz Builder & Publishing UI
  - Created `frontend/src/types/quiz.ts` and `frontend/src/services/quizApi.ts`.
  - Built `frontend/src/pages/teacher/QuizList.tsx`: Grid/table of teacher quizzes with status badges (Draft / Published), version numbers, question counts, marks, search, and a "Create Quiz" modal.
  - Built `frontend/src/pages/teacher/QuizBuilder.tsx`: Comprehensive split-screen quiz authoring workspace:
    - Left column: Assessment settings editor (schedule window, duration, attempt limit, backtracking, shuffling, multi-answer scoring policy, tab-switch warning & penalty configuration).
    - Right column: Question manager with live question count, total marks, difficulty badges, drag/up/down reordering, removal, and "Add Questions from Bank" modal trigger.
  - Built `frontend/src/pages/teacher/QuestionSelectorModal.tsx`: Searchable question bank browser with difficulty and type filters and batch selection.
  - Built `frontend/src/pages/teacher/QuizPreviewModal.tsx`: Pre-publication readiness checklist, metrics summary, and publish confirmation warning explaining version immutability.
  - Updated `frontend/src/pages/teacher/QuestionBank.tsx`, `QuestionModal.tsx`, and `CsvImportModal.tsx` to display and edit difficulty levels and accept `.xlsx` files.
  - Mounted `/teacher/quizzes` and `/teacher/quizzes/:quizId` routes in `frontend/src/App.tsx` and updated `Header.tsx`.
- **Action**: Comprehensive Testing & Verification
  - Created `backend/tests/test_quizzes_api.py` with 9 integration tests covering auth denial (401/403), cross-teacher isolation (404), draft lifecycle, invalid schedule rejection, bank question cloning & difficulty preservation, question reordering & removal, empty quiz publish rejection, and immutable version locking with draft forking.
  - Extended `backend/tests/test_csv_parser.py` to 15 unit tests covering genuine `.xlsx` generation, parsing, corrupt workbook rejection, difficulty validation, and defaults.
  - Extended `backend/tests/test_models.py` migration chain to verify head `0004_question_difficulty`.
  - Ran full backend pytest suite: all 71 tests passed in 4.12s.
  - Ran frontend linter (`oxlint`): 0 errors across 27 files.
  - Ran frontend production build (`npm run build`): passed in 709ms with 0 errors.

### 2026-10-23: Phase 5 - Student Roster Import, Quiz Assignment & Eligibility Enforcement
- **Context & Objectives**:
  - Implemented the full student roster ingestion, validation, and quiz assignment lifecycle for Quizdesk.
  - Implemented secure student identity matching against authoritative database records (`User` + `StudentProfile`) without trusting client inputs or treating roster rows as proof of identity.
  - Implemented a two-stage dry-run preview and transactional import workflow with revalidation, conflict rejection, and duplicate prevention.
  - Added full assignment management (listing with search & filters, single student assignment, status revocation/reactivation, and attempt-protected deletion).
  - Implemented a reusable server-side eligibility check verifying authenticated student identity, active status, assignment status, PRN alignment, and scheduling windows.
- **Action**: Data Model & Migration (DEC-018)
  - Extended `QuizAssignment` in `backend/app/models/roster.py` with `is_active: bool = True`, `revoked_at: datetime | None`, `revoked_by_id: UUID | None` (FK to `users.id`), relationship `revoked_by`, and index `ix_quiz_assignments_active` on `['quiz_id', 'is_active']`.
  - Authored migration `backend/alembic/versions/0005_assignment_lifecycle.py` chaining `0004_question_difficulty -> 0005_assignment_lifecycle`.
  - Tested migration chain: verified `0005_assignment_lifecycle -> 0004_question_difficulty -> 0003_question_bank -> 0002_integrity -> 0001_initial_schema`. Verified static offline SQL generation for both upgrade and downgrade.
- **Action**: Dual-Format Roster Spreadsheet Parsing & Template Generation
  - Created `backend/app/services/roster_parser.py`:
    - Validates strict headers: `prn,name,email,division`.
    - Preserves PRN as string (retaining leading zeros like `'00123'`).
    - Normalizes emails to lowercase trimmed strings.
    - Detects intra-file duplicate PRNs and duplicate emails with row-level actionable errors.
    - Limits parsing to 500 rows and 2MB file size.
    - Generates downloadable sample roster templates in both `.csv` and genuine `.xlsx` formats.
- **Action**: Student Identity Alignment & Two-Stage Ingestion Service
  - Created `backend/app/services/roster_service.py`:
    - Bounded bulk querying for candidate PRNs and emails to evaluate matching in a single database round-trip.
    - Categorizes candidates:
      - `matched`: User exists and `StudentProfile.prn` matches roster PRN (`assigned_student_id = user.id`).
      - `unregistered`: No user exists with that email or PRN (`assigned_student_id = None`; does NOT create unverified accounts).
      - `pending_profile`: User exists with that email but has not yet completed a student profile.
      - `conflict`: Account exists where email and PRN point to different records (blocks import with HTTP 422).
    - Dry-run preview (`POST /api/v1/quizzes/{id}/roster/preview`): parses file, performs identity matching, reports metrics and conflict flags with zero database mutations.
    - Transactional commit (`POST /api/v1/quizzes/{id}/roster/import`): revalidates file and current DB state within a transaction, creates or updates assignments additively, and emits an `AuditEvent`.
- **Action**: Assignment Management & Eligibility Check Endpoints
  - Created `backend/app/api/v1/endpoints/roster.py`:
    - `GET /api/v1/quizzes/{id}/roster/template`: Download CSV or Excel template.
    - `POST /api/v1/quizzes/{id}/roster/preview`: Dry-run roster validation.
    - `POST /api/v1/quizzes/{id}/roster/import`: Transactional roster commit.
    - `GET /api/v1/quizzes/{id}/assignments`: Filterable list of assigned students with summary metrics.
    - `POST /api/v1/quizzes/{id}/assignments`: Single student manual assignment.
    - `PATCH /api/v1/quizzes/{id}/assignments/{assignment_id}/status`: Revoke or reactivate an assignment with timestamp and teacher ID.
    - `DELETE /api/v1/quizzes/{id}/assignments/{assignment_id}`: Hard delete assignment; strictly blocked with HTTP 400 if historical attempts exist.
  - Created `backend/app/services/eligibility.py` & `backend/app/api/v1/endpoints/student_quiz.py`:
    - `GET /api/v1/student/quizzes/{id}/eligibility`: Authoritative eligibility check returning `{eligible, reason, opens_at, closes_at, duration_minutes, max_attempts}`.
    - Validates: authenticated active student, published quiz version, active assignment, PRN consistency, and active scheduling window.
    - Seamlessly auto-binds previously `unregistered` assignments when a student with matching email and PRN registers.
- **Action**: Teacher Frontend Roster & Eligibility Workspace
  - Created `frontend/src/types/roster.ts` and `frontend/src/services/rosterApi.ts`.
  - Created `frontend/src/pages/teacher/RosterTab.tsx`: Summary KPI cards, search, status filter, assignment table, revoke/reactivate controls, and attempt-safe delete modal.
  - Created `frontend/src/pages/teacher/RosterImportModal.tsx`: Two-stage import modal with file dropzone, format guide, summary metrics, conflict alert banners, row preview table with status pills, and confirm action.
  - Created `frontend/src/pages/teacher/AddStudentModal.tsx`: Single student manual entry modal with institutional field validation.
  - Integrated "Student Roster & Eligibility" tab into `frontend/src/pages/teacher/QuizBuilder.tsx`.
- **Action**: Automated Testing & Code Quality Verification
  - Created 33 new backend tests across 3 test suites:
    - `backend/tests/test_roster_parser.py`: 11 tests for CSV/XLSX, leading zeros, duplicates, headers, row limits, corrupt files, and template generation.
    - `backend/tests/test_roster_api.py`: 12 tests for auth/ownership isolation, preview dry-run (0 writes), transactional import, conflict rejection, single add, revoke/reactivate, attempt-protected delete, and search filtering.
    - `backend/tests/test_eligibility.py`: 10 tests for student role restriction, unpublished quiz rejection, unassigned/revoked rejection, identity mismatch denial, window timing, and auto-binding.
  - Updated `backend/tests/test_models.py` to verify migration chain head `0005_assignment_lifecycle`.
  - Ran full backend pytest suite: **104 passed in 5.18s**.
  - Ran frontend linter (`oxlint`): **0 errors across 32 files**.
  - Ran frontend production build (`tsc -b && vite build`): **passed in 1.52s with 0 errors**.

---

## 5. Commands Executed & Verified Outcomes

| Command | Working Directory | Exit Code | Result / Output Summary |
|---|---|---|---|
| Directory Inspection (`list_dir`) | `d:\ANUP\Quizdesk` | N/A | Returned: "Empty directory". |
| `git status` | `d:\ANUP\Quizdesk` | 1 | Returned: `fatal: not a git repository (or any of the parent directories): .git`. |
| `git status` (post user `git init`) | `d:\ANUP\Quizdesk` | 0 | Branch `main`, No commits yet, untracked files `AGENTS.md`, `docs/`. |
| `git config --get user.name; user.email` | `d:\ANUP\Quizdesk` | 0 | `Manmath Kornule <202401110045@mitaoe.ac.in>`. |
| `git check-ignore -v .env .env.local .venv/ node_modules/` | `d:\ANUP\Quizdesk` | 0 | Confirmed all 4 patterns matched ignore rules in `.gitignore`. |
| `git check-ignore -v .env.example backend/.env.example` | `d:\ANUP\Quizdesk` | 0 | Confirmed matched deliberate un-ignore rule `!**/.env.example`. |
| Trackability test with temporary `.env.example` and `.env` | `d:\ANUP\Quizdesk` | 0 | Confirmed `.env.example` appeared in `git status --short` and `.env` was ignored. |
| `git add .gitignore AGENTS.md docs/` | `d:\ANUP\Quizdesk` | 0 | Staged all 6 baseline project files. |
| `git commit -m "chore: establish project baseline"` | `d:\ANUP\Quizdesk` | 0 | Commit created: `7bdaff5` (root-commit, 6 files changed, 1002 insertions). |
| `git rev-parse HEAD` | `d:\ANUP\Quizdesk` | 0 | `7bdaff5e0412291a9c831d745437665f01c0232a`. |
| `python --version` | `d:\ANUP\Quizdesk` | 0 | Python 3.13.5. |
| `python -m venv .venv` | `d:\ANUP\Quizdesk` | 0 | Virtual environment created successfully in `.venv/`. |
| `.\.venv\Scripts\pip.exe install -r backend/requirements.txt` | `d:\ANUP\Quizdesk` | 0 | Installed all pinned packages into root `.venv`. |
| `.\.venv\Scripts\pip.exe install pyjwt==2.10.1` | `d:\ANUP\Quizdesk` | 0 | Installed PyJWT for HMAC-SHA256 token verification. |
| `.\.venv\Scripts\pip.exe install python-multipart==0.0.20` | `d:\ANUP\Quizdesk` | 0 | Installed python-multipart for file upload parsing. |
| `.\.venv\Scripts\pip.exe install openpyxl==3.1.5` | `d:\ANUP\Quizdesk` | 0 | Installed openpyxl for genuine Excel workbook support. |
| `.\.venv\Scripts\python.exe -m pytest -c backend/pytest.ini backend/tests -v` | `d:\ANUP\Quizdesk` | 0 | `104 passed in 5.18s` (all models, migrations, auth, profile, CORS, CSV & Excel parser, question bank, quiz builder, roster ingestion, and eligibility tests passing). |
| `npx -y create-vite@latest frontend --template react-ts` | `d:\ANUP\Quizdesk` | 0 | Scaffolded React + TypeScript project. |
| `npm install react-router-dom lucide-react; npm i -D tailwindcss @tailwindcss/vite` | `d:\ANUP\Quizdesk\frontend` | 0 | 50 packages installed with 0 vulnerabilities. |
| `npm install @supabase/supabase-js` | `d:\ANUP\Quizdesk\frontend` | 0 | Added Supabase browser client with 0 vulnerabilities. |
| `npm run lint` (oxlint) | `d:\ANUP\Quizdesk\frontend` | 0 | 0 errors across 32 files. |
| `npm run build` | `d:\ANUP\Quizdesk\frontend` | 0 | TypeScript check and Vite build passed in 1.52s. |
| `alembic -c backend/alembic.ini history` | `d:\ANUP\Quizdesk` | 0 | `0001_initial_schema -> 0002_integrity -> 0003_question_bank -> 0004_question_difficulty -> 0005_assignment_lifecycle (head)`. |
| `alembic -c backend/alembic.ini upgrade 0004_question_difficulty:0005_assignment_lifecycle --sql` | `d:\ANUP\Quizdesk` | 0 | Generated valid offline PostgreSQL DDL for assignment lifecycle columns, index, and FK. |
| `alembic -c backend/alembic.ini downgrade 0005_assignment_lifecycle:0004_question_difficulty --sql` | `d:\ANUP\Quizdesk` | 0 | Verified clean reversal DDL for migration 0005. |

---

## 6. Dependencies Added / Removed
- Added backend dependencies pinned in [`backend/requirements.txt`](file:///d:/ANUP/Quizdesk/backend/requirements.txt):
  - `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pyjwt==2.10.1`, `python-multipart==0.0.20`, `openpyxl==3.1.5`, `pytest`, `pytest-asyncio`, `httpx`.
- Added frontend dependencies in [`frontend/package.json`](file:///d:/ANUP/Quizdesk/frontend/package.json):
  - Runtime: `@supabase/supabase-js`, `react`, `react-dom`, `react-router-dom`, `lucide-react`.
  - Development: `tailwindcss`, `@tailwindcss/vite`, `vite`, `typescript`, `@types/react`, `@types/react-dom`, `oxlint`.

---

## 7. Tests Performed & Actual Results
- **Filesystem & Git Verification**:
  - Confirmed `.venv/`, `frontend/node_modules/`, and `frontend/dist/` are ignored by Git.
- **Backend Test Suite (Health, Models, Auth & Roles, Profile Endpoint, CORS, CSV/XLSX Parser, Question Bank API, Quizzes API, Roster Parser, Roster API, Eligibility API)**:
  - Executed: `.\.venv\Scripts\python.exe -m pytest -c backend/pytest.ini backend/tests -v`
  - Results: `104 passed in 5.18s`.
- **Frontend Linter & Production Build Verification**:
  - Executed: `npm run lint` (oxlint): 0 errors across 32 files.
  - Executed: `npm run build` (`tsc -b && vite build`): Successful compilation, 2043 modules transformed in 1.52s.
- **Alembic Offline Migration Checks**:
  - Verified `upgrade 0004_question_difficulty:0005_assignment_lifecycle --sql` and `downgrade 0005_assignment_lifecycle:0004_question_difficulty --sql`.

---

## 8. Known Issues, Risks & Unresolved Questions

### Known Risks & Modeling Trade-Offs:
1. **Question Bank Isolation via Deep Copy**: Reusable bank questions are cloned with their options when added to a quiz version. Bank updates do not propagate to quizzes, preserving historical assessment integrity.
2. **Published Quiz Mutability**: Modifying settings or questions on a published quiz automatically branches a new draft `QuizVersion`, leaving previous versions and student attempts attached to their original frozen snapshot.
3. **Additive Roster Re-Imports**: Re-importing a roster updates student details (name, division) without silently removing unlisted students. Deletions require explicit removal in the teacher UI, which is blocked if historical attempts exist.
4. **High-Concurrency Load Simulation**: Actual simultaneous 50+ student exam load testing is reserved for Phase 8 against a deployed PostgreSQL environment.

### Unresolved Questions / Future Confirmations:
- Live Supabase project credentials to be provided in `.env.local` and `.env` prior to staging deployment.

---

## 9. Deviations from Agreed Decisions
- **None**: All changes strictly adhere to DEC-001 through DEC-018.

---

## 10. Recommended Next Task

**Task**: **`TASK-601`: Active quiz delivery API (Sanitized Payload) (Phase 6)**
- Implement delivery of student exam payloads with stripped answer keys and explanations, attempt start window verification, single/multi attempt limits, and question/option randomization.








