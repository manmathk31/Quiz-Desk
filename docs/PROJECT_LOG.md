# Project Execution Log & Persistent Memory

This document is the single authoritative historical log and persistent memory for the **Quizdesk** project. It records verified actions, architectural milestones, command outcomes, repository evolution, and exact next steps.

---

## 1. Project Overview & Current Stage

- **Project Name**: Quizdesk
- **Core Purpose**: A high-reliability, real college quiz and assessment platform featuring separate student and teacher experiences. Engineered for scheduled examinations, strict academic integrity, automated grading, server-authoritative timings, and resilient autosaving under concurrent loads.
- **Current Development Stage**: **Phase 1: Repository Foundation & Toolchain Setup (In progress)**
- **Working Directory**: `d:\ANUP\Quizdesk`
- **Active Branch**: `main` (Git repository initialized)

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
| `.\.venv\Scripts\python.exe -m pytest -c backend/pytest.ini backend/tests -v` | `d:\ANUP\Quizdesk` | 0 | `5 passed in 1.34s`. |
| `npx -y create-vite@latest frontend --template react-ts` | `d:\ANUP\Quizdesk` | 0 | Scaffolded React + TypeScript project. |
| `npm install react-router-dom lucide-react; npm i -D tailwindcss @tailwindcss/vite` | `d:\ANUP\Quizdesk\frontend` | 0 | 50 packages installed with 0 vulnerabilities. |
| `npm run build` | `d:\ANUP\Quizdesk\frontend` | 0 | TypeScript check and Vite build passed in 727ms. |
| `alembic -c backend/alembic.ini history` | `d:\ANUP\Quizdesk` | 0 | `<base> -> 0001_initial_schema (head)`. |
| `alembic -c backend/alembic.ini upgrade head --sql` | `d:\ANUP\Quizdesk` | 0 | Generated valid offline PostgreSQL DDL for all 13 tables. |

---

## 6. Dependencies Added / Removed
- Added backend dependencies pinned in [`backend/requirements.txt`](file:///d:/ANUP/Quizdesk/backend/requirements.txt):
  - `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pytest`, `pytest-asyncio`, `httpx`.
- Added frontend dependencies in [`frontend/package.json`](file:///d:/ANUP/Quizdesk/frontend/package.json):
  - Runtime: `react`, `react-dom`, `react-router-dom`, `lucide-react`.
  - Development: `tailwindcss`, `@tailwindcss/vite`, `vite`, `typescript`, `@types/react`, `@types/react-dom`.

---

## 7. Tests Performed & Actual Results
- **Filesystem & Git Verification**:
  - Confirmed `.venv/`, `frontend/node_modules/`, and `frontend/dist/` are ignored by Git.
- **Backend Test Suite (Health & Models)**:
  - Executed: `.\.venv\Scripts\python.exe -m pytest -c backend/pytest.ini backend/tests -v`
  - Results:
    - `test_health_check_returns_ok PASSED [20%]`
    - `test_sqlalchemy_metadata_table_registration PASSED [40%]`
    - `test_unique_constraints_and_foreign_keys PASSED [60%]`
    - `test_enum_specifications PASSED [80%]`
    - `test_alembic_migration_chain PASSED [100%]`
    - Summary: `5 passed in 1.34s`.
- **Alembic Offline DDL Validation**:
  - Verified DDL generation for all 13 tables without database connection.
- **Frontend Production Build Verification**:
  - Executed: `npm run build` (`tsc -b && vite build`).
  - Result: Successful compilation, 1946 modules transformed in 727ms.

---

## 8. Known Issues, Risks & Unresolved Questions

### Known Risks & Modeling Trade-Offs:
1. **Live PostgreSQL Execution Untested in this Step**: No local PostgreSQL service is installed and Supabase credentials are not yet supplied. Validated offline via Alembic `--sql` DDL generation and metadata unit tests. Live database execution will take place in Phase 3 when Supabase credentials are configured in `.env`.
2. **Answer Selection Model Trade-off**: Stored in `attempt_answers.selected_option_ids` as a JSON array of UUIDs. This avoids schema changes between single-choice, multiple-choice, and true-false answers while maintaining foreign key integrity on questions.
3. **Immutability Trade-off**: Editing a published quiz creates a new `QuizVersion` rather than mutating existing rows, preserving historical attempt validity.

### Unresolved Questions / Future Confirmations:
- Exact Supabase project URL and keys to be configured via `.env` in Phase 3.

---

## 9. Deviations from Agreed Decisions
- **None**: All actions strictly complied with Phase 2 boundary constraints and confirmed decisions.

---

## 10. Recommended Next Task

**Task**: **`TASK-301`: FastAPI JWT verification middleware & Supabase Auth integration**
- Configure Supabase Auth client and FastAPI dependency for validating JWT signatures.
- Implement `@require_role(["teacher", "student", "admin"])` security guards.




