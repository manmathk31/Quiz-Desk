# Task Tracker

This document tracks all implementation tasks for **Quizdesk**. Each task is assigned a strict status, explicit acceptance criteria, and prerequisite dependencies.

### Status Legend
- `Not started`: Work has not commenced.
- `In progress`: Active development in progress.
- `Blocked`: Work cannot proceed until dependencies or external blockers are resolved.
- `Completed`: Verified and fully tested against acceptance criteria.

---

## Phase 0: Project Governance & Documentation Setup
**Goal**: Establish persistent project memory, decision registers, agent operating rules, and architectural blueprints before any code or scaffolding is created.

| Task ID | Task Title | Status | Dependencies | Verified Date |
|---|---|---|---|---|
| `TASK-001` | Workspace inspection & Git state verification | `Completed` | None | 2026-10-23 |
| `TASK-002` | Create `AGENTS.md` operating rules | `Completed` | `TASK-001` | 2026-10-23 |
| `TASK-003` | Create `docs/DECISIONS.md` register with confirmed ADRs | `Completed` | `TASK-001` | 2026-10-23 |
| `TASK-004` | Create `docs/ARCHITECTURE.md` blueprint | `Completed` | `TASK-003` | 2026-10-23 |
| `TASK-005` | Create `docs/TASK_TRACKER.md` with roadmap & acceptance criteria | `Completed` | `TASK-003` | 2026-10-23 |
| `TASK-006` | Create `docs/PROJECT_LOG.md` persistent memory | `Completed` | `TASK-002`, `TASK-003`, `TASK-004`, `TASK-005` | 2026-10-23 |

---

## Phase 1: Repository Foundation & Toolchain Setup
**Goal**: Initialize version control, environment isolation, ignore rules, and project directory structure without installing unvetted dependencies.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-101` | Git repository initialization & `.gitignore` creation | `Completed` | Phase 0 | - `git init` executed.<br>- Comprehensive `.gitignore` covering `.venv/`, `node_modules/`, `dist/`, `.env`, `*.pyc`, `__pycache__/`, coverage files.<br>- Initial commit with documentation files (verified commit `7bdaff5`). |
| `TASK-102` | Python virtual environment & backend scaffolding | `Completed` | `TASK-101` | - Isolated `.venv` created.<br>- FastAPI, Pydantic, SQLAlchemy, Alembic pinned in `backend/requirements.txt`.<br>- Health check endpoint (`GET /health`) implemented and verified (1 passed in 0.71s). |
| `TASK-103` | Frontend Vite + React + TypeScript scaffolding | `Completed` | `TASK-101` | - Vite React TS application scaffolded in `./frontend`.<br>- Tailwind CSS v4, React Router, Lucide React configured.<br>- Academic portal design shell with responsive layout.<br>- Production build verified (`tsc -b && vite build` built in 727ms). |
| `TASK-104` | Database schema & migration foundation | `Completed` | `TASK-102` | - 13 SQLAlchemy 2.x domain models defined.<br>- Alembic configured with dynamic DATABASE_URL and %(here)s/alembic.<br>- Initial migration `0001_initial_schema` and integrity hardening migration `0002_integrity` created and verified via pytest & offline SQL generation. |
| `TASK-105` | Database integrity & immutability audit | `Completed` | `TASK-104` | - Student assignment identity secured with dual unique constraints (`prn` & `email`).<br>- Published version immutability enforced with `ON DELETE RESTRICT` and `is_published` flag.<br>- Result release cleanly decoupled from internal attempt grading lifecycle.<br>- Check constraints and multi-answer scoring policies verified. |

---

## Phase 2: Database Schema & Migration Foundation
**Goal**: Establish code-first PostgreSQL schema with SQLAlchemy 2.x and version-controlled Alembic migrations.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-201` | Alembic migration harness setup | `Completed` | `TASK-102` | - Alembic initialized in `backend/alembic/`.<br>- Dynamic settings-backed configuration and offline SQL generation verified. |
| `TASK-202` | Core user profile & role schema definition | `Completed` | `TASK-201` | - Tables for `users`, `roles` (`student`, `teacher`, `admin`), and `student_profiles` with `prn` uniqueness constraints defined and tested. |
| `TASK-203` | Quiz, Question, and Option relational schema | `Completed` | `TASK-201` | - Tables for `quizzes`, `quiz_versions`, `questions`, `question_options`.<br>- Support for single MCQ, multi MCQ, True/False, and immutable version constraints. |
| `TASK-204` | Roster assignment & attempt tracking schema | `Completed` | `TASK-202`, `TASK-203` | - Tables for `quiz_assignments`, `quiz_attempts`, `attempt_answers`, `attempt_telemetry_events`, `grade_adjustments`, `audit_events`, `import_jobs`.<br>- Constraints and indexes verified in migrations `0001_initial_schema` and `0002_integrity`. |

---

## Phase 3: Authentication & Role-Based Access Control
**Goal**: Connect Supabase Auth, build backend token validation middleware, and enforce student/teacher boundaries.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-301A` | FastAPI JWT authentication foundation & role guards | `Completed` | `TASK-102`, `TASK-202` | - PyJWT installed and configured for Supabase HS256 JWTs.<br>- `get_current_user` extracts Bearer token, cryptographically validates signature, expiration, audience, and subject.<br>- Rejects missing/malformed/expired/unregistered/inactive tokens with 401.<br>- Authoritative user roles resolved from database `User.role` (JWT claims role spoofing prevented).<br>- Reusable role guards (`require_student`, `require_teacher`, `require_admin`, `require_faculty`) return 403 on role mismatch.<br>- Verified with 18 comprehensive auth unit tests. |
| `TASK-301B` | Live Supabase project credentials & user provisioning | `Not started` | `TASK-301A` | - Configure live Supabase URL, anon key, and JWT secret in `.env`.<br>- Implement user profile creation/sync hook when a Supabase user signs up. |
| `TASK-303` | Frontend authentication context & route guards | `Not started` | `TASK-103`, `TASK-301A` | - Supabase client integration for student login using institutional email.<br>- Protected routes redirect unauthorized users to login.<br>- Session tokens stored securely and refreshed automatically. |


---

## Phase 4: Teacher Portal: Question Bank & CSV Import Engine
**Goal**: Enable teachers to author quizzes manually or import validated question sets from CSV files.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-401` | Backend question CSV parser & validator | `Not started` | `TASK-203`, `TASK-302` | - Parses uploaded question CSVs.<br>- Validates headers, question types (single MCQ, multi MCQ, True/False), positive marks, and negative marks.<br>- Returns dry-run preview and line-specific error summaries before persisting. |
| `TASK-402` | Quiz builder & manual question CRUD endpoints | `Not started` | `TASK-203`, `TASK-302` | - REST endpoints to create, update, delete draft quizzes.<br>- Supports manual question composition, reordering, and mark configuration. |
| `TASK-403` | Quiz publication & version locking | `Not started` | `TASK-402` | - Publishing locks the quiz version as immutable.<br>- Subsequent modifications trigger version incrementing. |
| `TASK-404` | Teacher quiz authoring UI | `Not started` | `TASK-103`, `TASK-401`, `TASK-402` | - Clean, academic portal UI for creating quizzes, adding questions, and uploading CSVs with immediate error preview tables. |

---

## Phase 5: Student Roster Assignment Engine
**Goal**: Manage quiz eligibility strictly through per-quiz student CSV rosters.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-501` | Student roster CSV upload & validation API | `Not started` | `TASK-204`, `TASK-302` | - Enforces exact CSV headers: `prn,name,email,division`.<br>- Rejects conflicting duplicates and invalid email formats with informative error reports. |
| `TASK-502` | Student assignment persistence & access control | `Not started` | `TASK-501` | - Persists student assignment records linked to quiz ID.<br>- Verifies student attempt eligibility against assignment records (division is informational only). |
| `TASK-503` | Teacher roster management UI | `Not started` | `TASK-103`, `TASK-501` | - Drag-and-drop CSV upload for student rosters with preview table and confirmation action. |

---

## Phase 6: Assessment Delivery & Real-Time Autosave Engine
**Goal**: Deliver a focused, distraction-free test-taking interface with resilient server-authoritative autosave.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-601` | Active quiz delivery API (Sanitized Payload) | `Not started` | `TASK-204`, `TASK-302` | - Delivers question sets with stripped answer keys and explanations.<br>- Implements question and option randomization if enabled.<br>- Enforces attempt window check and single/multi attempt limit. |
| `TASK-602` | Server-authoritative autosave endpoint | `Not started` | `TASK-601` | - Accepts candidate answers asynchronously.<br>- Enforces deadline constraint: $\min(\text{start} + \text{duration}, \text{quiz\_close})$.<br>- Safely upserts responses and returns confirmation timestamp. |
| `TASK-603` | Distraction-free student quiz UI | `Not started` | `TASK-103`, `TASK-601`, `TASK-602` | - Minimalist, high-focus exam layout on desktop and mobile.<br>- Background debounced autosave with clear "Saved" indicators.<br>- Seamless recovery upon browser reload or reconnection. |
| `TASK-604` | Tab-switch telemetry & warning system | `Not started` | `TASK-603` | - Clearly discloses monitoring rules to student prior to start.<br>- Records tab-switch telemetry timestamps.<br>- Enforces configured warning dialogs and teacher-defined deduction flags. |
| `TASK-605` | Attempt finalization & auto-submit on expiry | `Not started` | `TASK-602`, `TASK-603` | - Server finalizes attempt when time expires or student explicitly submits.<br>- Status transitions to `SUBMITTED`. |

---

## Phase 7: Evaluation, Grading, Result Management & Audit Trails
**Goal**: Automated scoring against answer keys, teacher review dashboard, score adjustments with audit logs, and controlled result release.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-701` | Automated grading engine | `Not started` | `TASK-605` | - Calculates raw score based on correct options, partial credit (for multi-answer), and negative marking.<br>- Sets initial result status to `WITHHELD`. |
| `TASK-702` | Teacher review dashboard & CSV export | `Not started` | `TASK-701` | - Teacher views grade distribution, candidate attempt breakdown, and tab-switch telemetry.<br>- Export full results to CSV. |
| `TASK-703` | Manual grade adjustment API with mandatory audit log | `Not started` | `TASK-702` | - Adjusting marks requires mandatory text rationale.<br>- Inserts immutable audit record in `audit_logs` table. |
| `TASK-704` | Result release workflow & student score view | `Not started` | `TASK-702`, `TASK-703` | - Teacher triggers release of results.<br>- Students can view only their personal total marks; answer keys remain protected. |

---

## Phase 8: Testing, Security Verification & Concurrent Load Simulation
**Goal**: Comprehensive test coverage across backend, frontend, end-to-end user flows, and realistic concurrent-load testing.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-801` | Backend unit and API integration tests | `Not started` | Phase 2 - 7 | - >85% branch coverage with `pytest` and `httpx`.<br>- All edge cases (deadlines, duplicate submissions, negative scores) covered. |
| `TASK-802` | Frontend unit and component tests | `Not started` | Phase 3 - 7 | - Component tests for quiz runner, autosave debouncer, and timer with `Vitest`. |
| `TASK-803` | End-to-end user flows with Playwright | `Not started` | `TASK-801`, `TASK-802` | - Automated E2E tests for Teacher: Create Quiz -> Import Questions -> Import Roster -> Release Results.<br>- Automated E2E tests for Student: Login -> Start Attempt -> Autosave -> Submit -> View Score. |
| `TASK-804` | High-concurrency load testing | `Not started` | `TASK-803` | - Simulated synchronized exam start (hundreds of virtual students) and burst autosave traffic.<br>- Sub-200ms p95 latency under target concurrency verified. |

---

## Phase 9: Administrative Dashboard & Institutional Governance
**Goal**: Dedicated administrator portal for institution-wide analytics, teacher account provisioning, and audit oversight. *(Deferred to post-MVP)*

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-901` | Institutional administrator portal | `Not started` | Phase 8 | - RBAC-protected portal for managing teacher accounts and auditing institutional assessment logs. |
