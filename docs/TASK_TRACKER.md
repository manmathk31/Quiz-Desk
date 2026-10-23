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
| `TASK-301B` | Authentication integration readiness review | `Completed` | `TASK-301A` | - Signing configuration audited (HS256 native support, asymmetric public key support).<br>- Non-self-promoting user provisioning design established (student self-signup, administrative teacher/admin provisioning).<br>- Frontend and backend secret separation verified with `frontend/.env.example`.<br>- Minimum live integration prerequisites documented. |
| `TASK-301C` | Live Supabase project credentials & database connection | `Blocked` | `TASK-301B` | - Configure live Supabase URL, anon key, and JWT secret in `.env`.<br>- Apply migrations to live PostgreSQL database. |
| `TASK-303` | Frontend authentication context & route guards | `Completed` | `TASK-103`, `TASK-301A` | - `@supabase/supabase-js` integrated with graceful fallback for unconfigured environments.<br>- `AuthProvider` & `useAuth` handle session hydration, subscription cleanup, sign-in, and sign-out.<br>- Role resolved strictly from backend endpoint (`/api/v1/users/me`), remaining unknown when endpoint is pending (no guessing from client metadata).<br>- `RequireAuth` and `RequireRole` route guards prevent content flash and enforce role boundaries.<br>- Integrated into React Router with minimal placeholder routes (`/login`, `/unauthorized`, `/student/portal`, `/teacher/portal`).<br>- Verified via `tsc -b && vite build` (746ms). |
| `TASK-302` | Backend profile endpoint & API router | `Completed` | `TASK-301A` | - Versioned API router structure under `backend/app/api/v1/` mounted at `/api/v1` in `backend/app/main.py`.<br>- `GET /api/v1/users/me` endpoint implemented reusing existing `get_current_active_user` dependency.<br>- Returns strictly allowed fields: `id`, `email`, `name`, `role`, `is_active` via `UserResponse` Pydantic schema.<br>- Authoritative role resolved from DB; rejects client role tampering or query overrides.<br>- Missing/invalid tokens return 401 Unauthorized.<br>- `GET /health` preserved unchanged.<br>- 13 dedicated API unit tests added (36 total tests passing). |
| `TASK-304` | Complete frontend–backend authentication integration | `Completed` | `TASK-302`, `TASK-303` | - `AuthContext` fetches `/api/v1/users/me` with active token on session hydration and state changes.<br>- Race-condition protection via `activeTokenRef` and `isMountedRef` discards stale in-flight requests.<br>- HTTP 401 and 403 explicitly clear profile and authoritative role, preventing stale privilege retention.<br>- `RequireAuth` and `RequireRole` prevent content flash and block unauthorized or unverified sessions.<br>- Backend `CORSMiddleware` configured with restricted local development origins and verified with preflight tests.<br>- All 38 backend tests and frontend type-check/build passed. |




---

## Phase 4: Teacher Portal: Question Bank & CSV Import Engine
**Goal**: Enable teachers to author quizzes manually or import validated question sets from CSV files.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-401` | Teacher Question Bank & CSV Import Engine (Milestone 4A) | `Completed` | `TASK-203`, `TASK-302` | - Migration `0003_question_bank` adds teacher ownership (`created_by_id`) and makes `quiz_version_id` nullable for reusable bank questions while preserving published version immutability.<br>- CSV parser handles UTF-8 BOM, required headers, single MCQ, multi MCQ, True/False, positive/negative marks, duplicate option checks, and 200 row / 2MB file limits.<br>- Authenticated API endpoints under `/api/v1/question-bank` (pagination, CRUD, CSV preview, transactional import, template download).<br>- Cross-teacher isolation and student role denial (403 Forbidden) strictly enforced.<br>- Teacher UI (`QuestionBank.tsx`, `QuestionModal.tsx`, `CsvImportModal.tsx`) with row-level error reporting, preview table, and confirmation step.<br>- Verified with 20 new tests (58 total backend tests passing) and clean frontend build. |

| `TASK-402` | Quiz builder & question management endpoints (Milestone 4B) | `Completed` | `TASK-203`, `TASK-302`, `TASK-401` | - REST endpoints under `/api/v1/quizzes` to list, create, update, delete draft quizzes.<br>- Supports settings configuration: schedule windows, duration, attempt limit, backtracking, shuffling, multi-answer policy, tab-switch warnings/penalties.<br>- Deep-clones selected Question Bank items into version-bound questions to isolate quiz drafts from bank edits.<br>- Question removal and sequence reordering (`PUT /questions/order`).<br>- Multi-tenant cross-teacher isolation (404) and student role rejection (403). |
| `TASK-403` | Immutable quiz publishing & difficulty support (Milestone 4B) | `Completed` | `TASK-402` | - Constrained `QuestionDifficulty` enum (`easy`, `medium`, `hard`) with DB migration `0004_question_difficulty`, index, and check constraint.<br>- Dual CSV + genuine `.xlsx` spreadsheet parser via `openpyxl` with row-level validation.<br>- Atomic server-side pre-publication validation (checks question presence, options completeness, and scheduling sanity).<br>- Version immutability: published versions are permanently frozen; subsequent draft edits automatically branch a new `QuizVersion` (incrementing version number). |
| `TASK-404` | Teacher quiz builder & publishing UI (Milestone 4B) | `Completed` | `TASK-103`, `TASK-401`, `TASK-402`, `TASK-403` | - Comprehensive teacher UI: `QuizList.tsx`, `QuizBuilder.tsx`, `QuestionSelectorModal.tsx`, `QuizPreviewModal.tsx`.<br>- Question Bank browser with search, type and difficulty filters, and batch selection.<br>- In-builder question ordering controls, difficulty badges, marks summary, and settings editor.<br>- Pre-publication checklist modal with publish confirmation warning.<br>- Verified through 71 backend tests, 0 linter errors, and clean frontend production build. |


---

## Phase 5: Student Roster Assignment Engine
**Goal**: Manage quiz eligibility strictly through per-quiz student CSV/XLSX rosters, secure identity alignment, and server-authoritative eligibility enforcement.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-501` | Student roster CSV & XLSX upload & validation engine | `Completed` | `TASK-204`, `TASK-302` | - Enforces strict headers: `prn,name,email,division` for both CSV and genuine `.xlsx` workbooks.<br>- Preserves PRNs as strings (retains leading zeros like `'00123'`).<br>- Normalizes emails to lowercase trimmed strings.<br>- Detects intra-file duplicate PRNs and duplicate emails with row-level actionable errors.<br>- Enforces 2MB file limit and 500 row maximum.<br>- Downloadable CSV and Excel sample templates with format instructions. |
| `TASK-502` | Student assignment persistence, identity alignment & server eligibility | `Completed` | `TASK-501` | - Migration `0005_assignment_lifecycle` adds `is_active`, `revoked_at`, `revoked_by_id`, and `ix_quiz_assignments_active`.<br>- Two-stage import workflow: dry-run preview (`POST /api/v1/quizzes/{id}/roster/preview` with 0 DB writes) and transactional commit (`POST /api/v1/quizzes/{id}/roster/import`).<br>- Identity matching: matched (profile PRN aligns), unregistered (`assigned_student_id = None`, does not create or elevate accounts), and identity conflict (PRN/email mismatch with existing account blocks import with 422).<br>- Additive import semantics: updates names/divisions/linked IDs without duplicating rows or silently revoking omitted students.<br>- Assignment management endpoints: list with search & filter, single add, revoke/reactivate, and attempt-protected delete (blocks deletion if attempts exist).<br>- Reusable server-side eligibility check (`GET /api/v1/student/quizzes/{id}/eligibility` and `check_student_quiz_eligibility`) verifying active student, published quiz, active assignment, and schedule window.<br>- Full audit event logging for roster imports, additions, and status changes. |
| `TASK-503` | Teacher roster management UI & workflow | `Completed` | `TASK-103`, `TASK-501`, `TASK-502` | - Integrated "Student Roster & Eligibility" tab in `QuizBuilder.tsx`.<br>- Two-stage import modal (`RosterImportModal.tsx`) with file upload, summary KPI cards, conflict warnings, row preview table, and explicit confirmation.<br>- Add single student modal (`AddStudentModal.tsx`) with PRN and email validation.<br>- Roster dashboard (`RosterTab.tsx`) with live stats, search, status filter, CSV/Excel template downloaders, and revoke/reactivate/delete controls with attempt safety warning.<br>- Verified with 33 new backend tests (104 total backend tests passing), 0 linter errors, and clean frontend production build. |

---

## Phase 6: Assessment Delivery & Real-Time Autosave Engine
**Goal**: Deliver a focused, distraction-free test-taking interface with resilient server-authoritative autosave, timers, telemetry, and submission.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-601` | Active quiz delivery API (Sanitized Payload) | `Completed` | `TASK-204`, `TASK-302` | - Migration `0006_attempt_shuffling` adds `question_order`, `option_order`, `client_timestamp`, and `ix_quiz_attempts_student_status`.<br>- Delivers question sets with stripped answer keys and explanations through `SanitizedQuestionResponse` and `SanitizedOptionResponse`.<br>- Pinned question and option shuffling persisted on `QuizAttempt` across reconnects and refreshes.<br>- Enforces schedule windows, max attempt limits, and cross-student isolation. |
| `TASK-602` | Server-authoritative autosave endpoint | `Completed` | `TASK-601` | - Targeted `PUT /api/v1/student/attempts/{id}/answers/{question_id}` endpoint.<br>- Enforces server-authoritative deadline $\min(\text{start} + \text{duration}, \text{close})$; late writes rejected with 409 Conflict.<br>- Out-of-order delayed HTTP writes safely rejected via monotonic `client_timestamp`.<br>- Validates single-choice (max 1 option), True/False, and multiple-choice constraints. |
| `TASK-603` | Distraction-free student quiz UI | `Completed` | `TASK-103`, `TASK-601`, `TASK-602` | - Student portal dashboard (`StudentDashboard.tsx`) with assigned quiz cards, availability status, and resume actions.<br>- High-contrast, focused test environment (`ActiveAssessment.tsx`) with question palette, review flags, and navigation.<br>- Synchronized server countdown timer with automatic expiry submission.<br>- Background debounced autosave with clear `Saving...`, `All answers saved`, and `Save failed` indicators.<br>- Seamless session resumption upon browser reload or reconnection without timer resets. |
| `TASK-604` | Tab-switch telemetry & warning system | `Completed` | `TASK-603` | - Listens to `visibilitychange` and window `blur` events.<br>- Server endpoint (`POST /telemetry`) increments `tab_switch_count` and checks threshold.<br>- Discloses rules to students and displays warning banner when limit exceeded.<br>- Applies configured score deductions during final grading if configured. |
| `TASK-605` | Attempt finalization & submission engine | `Completed` | `TASK-602`, `TASK-603` | - Shared idempotent finalization path (`submit_and_finalize_attempt`) for manual and expired submissions.<br>- Server-authoritative grading supporting Single Choice, True/False, and Multi-Answer policies (`all_or_nothing`, `partial_no_penalty`, `partial_with_penalty`).<br>- Results held withheld until teacher release (`total_score` and answer keys concealed from student).<br>- Completion screen (`AssessmentCompletion.tsx`) with server verification notice.<br>- Verified with 14 dedicated backend tests (118 total backend tests passing), 0 linter errors, and clean frontend production build. |

---

## Phase 7: Evaluation, Grading, Result Management & Audit Trails
**Goal**: Automated scoring against answer keys, teacher review dashboard, score adjustments with audit logs, and controlled result release.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-701` | Automated grading engine | `Completed` | `TASK-605` | - Calculates raw score based on correct options, partial credit (for multi-answer policies: `all_or_nothing`, `partial_no_penalty`, `partial_with_penalty`), negative marking, and tab-switch penalties.<br>- Sets initial result status to withheld (`is_results_released=False`). |
| `TASK-702` | Teacher review dashboard & CSV export | `Completed` | `TASK-701` | - Teacher views grade distribution, summary metrics (average, min, max, submitted, in-progress), candidate attempt breakdown, question responses with answer keys, and tab-switch telemetry.<br>- Export full results to CSV with formula injection sanitization. |
| `TASK-703` | Manual grade adjustment API with mandatory audit log | `Completed` | `TASK-702` | - Adjusting marks requires mandatory text rationale (min 3 chars).<br>- Preserves previous scores and revision history in `grade_adjustments` table.<br>- Inserts immutable audit record in `audit_events` table.<br>- Rejects in-progress attempts and scores outside $[0, \text{max\_marks}]$. |
| `TASK-704` | Result release workflow & student score view | `Completed` | `TASK-702`, `TASK-703` | - Teacher triggers release of results idempotently.<br>- Prior to release, student inquiries return 403 Forbidden with score withheld.<br>- Following release, students can view only their personal total score and completion status; answer keys and other students' marks remain protected. |

---

## Phase 8A: Assessment Proctoring Hardening, Configurable Penalties & Student Violation UX
**Goal**: Strongest practical, fair, transparent, and maintainable browser-based proctoring controls, configurable penalties, policy snapshots, readiness checks, and teacher telemetry diagnostics.

| Task ID | Task Title | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|
| `TASK-801A` | Assessment Proctoring Hardening & Configurable Penalties | `Completed` | Phase 6, Phase 7 | - Migration `0007_proctoring_hardening.py` adding check constraints and proctoring fields to `quiz_versions`, `quiz_attempts`, and `attempt_telemetry_events`.<br>- Configurable free violations ($F$), deduction rate ($D$, supporting half marks e.g. 0.5), and cumulative cap ($C$).<br>- Authoritative penalty formula: $\text{chargeable} = \max(0, V - F)$, $\text{deduction} = \min(\text{chargeable} \times D, C, \max(0, S))$, $\text{final} = \max(0, S - \text{deduction})$, guaranteed non-negative score.<br>- Server-authoritative telemetry hardening: idempotency via `client_event_id`, paired blur/switch deduplication within 1000ms, rate limiting, and rejection of invalid/fake event types.<br>- Pre-quiz readiness screen (`AssessmentReadinessModal.tsx`) disclosing all rules, verifying browser capabilities and Fullscreen API support, and requiring explicit confirmation.<br>- Active assessment controls (`ActiveAssessment.tsx`): scoped clipboard/contextmenu prevention, fullscreen enforcement with exit prompt, DevTools shortcut intercept, and live violation pill.<br>- Teacher QuizBuilder proctoring settings card and QuizResults telemetry diagnostics modal.<br>- Verified with 137 backend tests passing, 0 frontend linter errors, and clean frontend production build. |

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
