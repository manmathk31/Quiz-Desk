# Decision Register (ADR)

This document tracks all formal architectural and product decisions for **Quizdesk**. Each decision is numbered sequentially, marked with a definitive status, and accompanied by its technical rationale and implications.

### Status Definitions:
- **`Proposed`**: Under evaluation; not yet agreed or implemented.
- **`Confirmed`**: Formally agreed and binding for all development.
- **`Superseded`**: Replaced or updated by a newer confirmed decision.

---

## Decision Index

| ID | Title | Status | Date |
|---|---|---|---|
| [DEC-001](#dec-001-project-scope-and-core-architecture) | Project Scope and Modular Monolith Architecture | `Confirmed` | 2026-10-23 |
| [DEC-002](#dec-002-technology-stack-selection) | Technology Stack Selection | `Confirmed` | 2026-10-23 |
| [DEC-003](#dec-003-environment-isolation-and-secrets-policy) | Environment Isolation and Secrets Policy | `Confirmed` | 2026-10-23 |
| [DEC-004](#dec-004-visual-design-system-and-academic-ux) | Visual Design System and Academic UX | `Confirmed` | 2026-10-23 |
| [DEC-005](#dec-005-authentication-identity-and-role-enforcement) | Authentication, Identity, and Role Enforcement | `Confirmed` | 2026-10-23 |
| [DEC-006](#dec-006-question-types-and-csv-import-management) | Question Types and CSV Import Management | `Confirmed` | 2026-10-23 |
| [DEC-007](#dec-007-student-roster-assignment-via-per-quiz-csv) | Student Roster Assignment via Per-Quiz CSV | `Confirmed` | 2026-10-23 |
| [DEC-008](#dec-008-quiz-configuration-timing-and-lifecycle) | Quiz Configuration, Timing, and Lifecycle | `Confirmed` | 2026-10-23 |
| [DEC-009](#dec-009-active-assessment-engine-autosave-and-telemetry) | Active Assessment Engine, Autosave, and Telemetry | `Confirmed` | 2026-10-23 |
| [DEC-010](#dec-010-result-management-review-and-audit-trails) | Result Management, Review, and Audit Trails | `Confirmed` | 2026-10-23 |
| [DEC-011](#dec-011-administrative-governance-staging) | Administrative Governance Staging | `Confirmed` | 2026-10-23 |
| [DEC-012](#dec-012-in-portal-communications-policy) | In-Portal Communications Policy | `Confirmed` | 2026-10-23 |
| [DEC-013](#dec-013-security-authorization-and-load-testing-standards) | Security, Authorization, and Load Testing Standards | `Confirmed` | 2026-10-23 |
| [DEC-014](#dec-014-database-integrity-constraints-immutability-and-result-release-architecture) | Database Integrity Constraints & Immutability | `Confirmed` | 2026-10-23 |
| [DEC-015](#dec-015-authentication-integration-readiness--non-self-promoting-user-provisioning) | Authentication Readiness & Non-Self-Promoting Provisioning | `Confirmed` | 2026-10-23 |
| [DEC-016](#dec-016-question-difficulty-classification-and-dual-format-spreadsheet-ingestion-csv-and-xlsx) | Question Difficulty & Dual-Format Ingestion | `Confirmed` | 2026-10-23 |
| [DEC-017](#dec-017-teacher-quiz-builder-question-cloning-isolation-and-immutable-version-lifecycle) | Teacher Quiz Builder & Version Lifecycle | `Confirmed` | 2026-10-23 |
| [DEC-018](#dec-018-student-roster-ingestion-identity-alignment-and-server-authoritative-eligibility) | Student Roster Ingestion & Eligibility Gate | `Confirmed` | 2026-10-23 |
| [DEC-019](#dec-019-secure-student-assessment-engine-shuffling-persistence-autosave-invariants-and-authoritative-grading) | Secure Assessment Delivery, Autosave & Grading | `Confirmed` | 2026-10-23 |
| [DEC-020](#dec-020-teacher-results-management-score-adjustments-controlled-release-and-csv-export) | Teacher Results, Adjustments, Release & Export | `Confirmed` | 2026-10-23 |
| [DEC-021](#dec-021-assessment-proctoring-hardening-configurable-penalties--audit-diagnostics) | Assessment Proctoring Hardening, Configurable Penalties & Audit Diagnostics | `Confirmed` | 2026-10-23 |

---

### DEC-001: Project Scope and Modular Monolith Architecture
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**: Develop Quizdesk as a modular monolith consisting of a modern single-page application (SPA) frontend and a unified Python backend service, rather than microservices.
- **Rationale**: A real college assessment platform demands transactional integrity, predictable latency under synchronized student traffic, and low operational overhead. A modular monolith provides clean domain separation without the networking complexity, distributed transactions, and deployment friction of microservices.
- **Implications**: The backend codebase will be organized into well-isolated domain modules (e.g., `auth`, `quizzes`, `assessments`, `grading`, `roster`, `audit`) with clear interface boundaries to allow future decomposition if ever required.

---

### DEC-002: Technology Stack Selection
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**: Adopt the following core technology stack:
  - **Frontend**: React (v18+), TypeScript, Vite, Tailwind CSS, React Router.
  - **Backend**: Python 3.11+, FastAPI, Pydantic (v2), SQLAlchemy (v2 async/sync), Alembic for schema migrations.
  - **Database & Auth**: PostgreSQL managed via Supabase; Supabase Auth for identity management.
  - **Testing**:
    - Backend: `pytest`, `pytest-asyncio`, and `httpx`.
    - Frontend: `Vitest`, `@testing-library/react`.
    - End-to-End: `Playwright`.
- **Rationale**: 
  - FastAPI + Pydantic provides type-safe high-throughput asynchronous request handling and OpenAPI documentation.
  - React + TypeScript + Vite ensures fast build cycles and strict type contracts across the UI.
  - Supabase provides enterprise PostgreSQL with Row-Level Security capabilities and robust token-based authentication.
- **Implications**: Toolchains must be pinned in version management files (`package.json`, `pyproject.toml` or `requirements.txt`). Frontend and backend remain cleanly decoupled over RESTful JSON APIs.

---

### DEC-003: Environment Isolation and Secrets Policy
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**: All Python dependencies must run in a dedicated, isolated virtual environment (`.venv`). Secrets, local credentials, and environment-specific `.env` files must never be committed to source control.
- **Rationale**: Prevents host environment pollution, dependency divergence across developer systems, and catastrophic credential leaks.
- **Implications**: `.gitignore` must strictly ignore `.venv/`, `__pycache__/`, `.env`, `*.pyc`, `dist/`, and local coverage artifacts. Sample configurations will be provided solely as `.env.example` with empty placeholder values.

---

### DEC-004: Visual Design System and Academic UX
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**: Build an institutional, minimalist academic portal UI adhering to:
  - Surfaces: White (`#FFFFFF`) and crisp light-grey (`#F8FAFC`, `#F1F5F9`) backgrounds.
  - Structural elements: Deep navy (`#0F172A`, `#1E293B`) headers, sidebars, and primary typography.
  - Action elements: Restrained, accessible primary blue (`#2563EB`) buttons and focal links.
  - Feedback indicators: Balanced green (`#16A34A`) for success, amber for warnings, and muted red for destructive actions.
  - Strict styling constraints: No decorative gradients, no unnecessary animations, no exaggerated drop-shadows or pill-shaped cards. Clean typography (e.g., Inter), generous spacing, legible tables, and accessible high-contrast forms.
  - Responsive layout: Dedicated support for both desktop workstation screens and mobile smartphone screens.
  - Active Quiz View: A distraction-free, focused test-taking environment minimizing cognitive load and peripheral distractions.
- **Rationale**: Academic testing requires maximum legibility, zero distracting visual fluff, high accessibility standards, and calm user focus under timed exam pressure.
- **Implications**: Tailwind CSS configuration will define an explicit color token palette and typography scales enforcing these constraints across all UI components.

---

### DEC-005: Authentication, Identity, and Role Enforcement
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**: 
  - Students authenticate using institutional email and password via Supabase Auth.
  - Student PRN (Permanent Registration Number) is strictly an academic identifier, never a password or credential.
  - Teacher and proctor roles are provisioned solely by authorized administrators; self-registration of teacher accounts is strictly prohibited.
  - Backend FastAPI middleware must verify JWT signatures on every protected endpoint and enforce database-backed role permissions and resource ownership.
- **Rationale**: Prevents privilege escalation and identity spoofing. Treating PRN as a public academic identifier rather than a secret ensures clear separation between identification and authentication.
- **Implications**: Supabase Auth handles password hashing and session tokens; backend user profiles store verified roles (`student`, `teacher`, `admin`) and link to academic rosters.

---

### DEC-006: Question Types and CSV Import Management
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - The assessment engine must support:
    1. Single-answer Multiple Choice Questions (MCQ).
    2. Multiple-answer Multiple Choice Questions (Multi-MCQ).
    3. True / False questions.
  - Teachers can create questions manually via form UI or bulk-import via CSV.
  - All CSV imports must undergo dry-run validation with line-by-line error previews before committing records to the database.
  - Each question supports configurable marks and scoring rules (including partial or negative marking options).
  - Published quiz versions are immutable; edits to published quizzes generate an explicit new version to protect ongoing attempt integrity.
- **Rationale**: Prevents data corruption during bulk imports and guarantees mathematical fairness and auditability for published tests.
- **Implications**: A dedicated CSV parsing and validation service must be implemented on the backend with comprehensive schema checks and error reporting.

---

### DEC-007: Student Roster Assignment via Per-Quiz CSV
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - Student access to quizzes is governed strictly by an uploaded student roster CSV containing exactly four required columns: `prn`, `name`, `email`, `division`.
  - The system must validate duplicate PRNs, duplicate emails, and malformed rows during upload.
  - Direct assignment records created from the CSV grant assessment access.
  - Student `division` is treated solely as an organizational grouping metadata attribute, **not** as an access-control mechanism.
- **Rationale**: Allows teachers flexibility to assign quizzes to specific batches, cross-division groups, or repeaters without complex institutional directory sync dependencies.
- **Implications**: The database schema must feature a dedicated `quiz_assignments` table linking student profiles (or PRNs) directly to the specific quiz ID, validated against active user identities.

---

### DEC-008: Quiz Configuration, Timing, and Lifecycle
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - Quiz settings must support:
    - Scheduled availability window: start time (`opens_at`) and end time (`closes_at`).
    - Per-attempt duration timer (e.g., 45 minutes).
    - Configurable attempt limits (default 1 attempt for graded exams).
    - Navigation policy: optional free navigation or forward-only/no-backtracking mode.
    - Question and option randomization/shuffling per attempt.
    - Negative marking per question and configurable multi-answer scoring policies.
  - Attempt Expiry Rule: An attempt strictly expires at the earlier of:
    $$\text{Deadline} = \min(\text{Attempt Start} + \text{Duration}, \text{Quiz Closing Time})$$
  - Expiry immediately finalizes the attempt on the server using all successfully autosaved answers.
  - Published quiz revisions create new versions. Cancelled assessments preserve all historical attempt data; archived quizzes are retained and never hard-deleted.
- **Rationale**: Eliminates student loopholes regarding quiz closing times vs. individual attempt durations and ensures historical academic records remain fully auditable.
- **Implications**: The server maintains authoritative timestamps. Client-side clocks are never trusted for test duration or deadline enforcement.

---

### DEC-009: Active Assessment Engine, Autosave, and Telemetry
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - The server is the single source of truth for time remaining, question sets, and evaluation.
  - Active question delivery payloads sent to the client must **never** include correct answers or explanation fields.
  - Answers must autosave safely in the background on every interaction or periodic interval without blocking user input.
  - Students must be able to seamlessly resume an in-progress attempt following a page refresh, browser crash, or temporary network disconnect, provided the attempt deadline has not expired.
  - Tab-switching detection: Configurable warning thresholds and score deductions may be enabled by the teacher, but must be clearly disclosed to the student prior to starting the assessment. Tab-switch events must be treated as telemetry signals requiring teacher review, not infallible proof of academic dishonesty.
- **Rationale**: Eliminates client-side answer inspection via browser DevTools, protects student work against accidental data loss or connectivity hiccups, and provides fair, transparent proctoring telemetry.
- **Implications**: Autosave endpoints must handle high-frequency idempotent writes; telemetry logs must record timestamped events without automatically disqualifying candidates without human oversight.

---

### DEC-010: Result Management, Review, and Audit Trails
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - Results are held in a withheld state upon completion until explicitly released by the teacher.
  - Upon release, students can view only their personal total score and marks earned; answer keys and other students' scores remain concealed unless explicitly authorized.
  - Teachers have access to aggregated score distribution analytics, item analysis, and student-level result CSV exports.
  - Any post-hoc manual grade adjustments by a teacher require a mandatory textual reason and generate an immutable audit log entry.
- **Rationale**: Prevents premature answer sharing between exam batches, protects student privacy, and ensures academic accountability for altered scores.
- **Implications**: The database schema must maintain an `audit_logs` / `grade_adjustments` table recording user ID, target attempt, previous score, new score, reason, and timestamp.

---

### DEC-011: Administrative Governance Staging
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - A dedicated administrator portal for institutional configuration, system health, and teacher account provisioning will be built in Phase 2, after core teacher and student workflows are operational.
  - However, all architectural foundations—backend role-based authorization guards, audit logging structures, and security boundaries—must be established immediately in Phase 1.
  - Administrative security must never rely on hidden URLs or obscurity, and must never expose raw, unrestricted database manipulation.
- **Rationale**: Keeps early focus on critical assessment delivery while ensuring the architecture does not require invasive refactoring when full institutional administration is introduced.
- **Implications**: Permission checks will support an `admin` role from the very first backend authentication middleware implementation.

---

### DEC-012: In-Portal Communications Policy
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**: Automated external email/SMS notifications and reminder alerts are excluded from the initial platform milestone. All assessment announcements, deadlines, status updates, and result alerts must be communicated via the in-portal user interface.
- **Rationale**: Avoids premature integration dependencies on external third-party transactional mail providers (SendGrid, Postmark, AWS SES), domain DNS verification, and deliverability complexities.
- **Implications**: The frontend dashboard will display prominent assessment schedules, upcoming deadlines, and announcement banners.

---

### DEC-013: Security, Authorization, and Load Testing Standards
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - Every protected API endpoint must enforce explicit role-based access control and ownership verification (e.g., verifying a student owns the attempt being updated).
  - Defensive measures must prevent:
    - Inspection of answer keys in transit or client state.
    - Submission of answers past the authoritative server deadline.
    - Race conditions or duplicate submissions.
    - Path traversal or injection in CSV import/export handlers.
  - Realistic concurrent-load testing simulating peak synchronized exam starts and autosave bursts must be executed and verified before the platform is deployed for high-stakes examinations.
- **Rationale**: College exams experience severe synchronization spikes (e.g., hundreds of students starting and submitting at the exact same minute). Security and concurrency resilience must be proven empirically rather than assumed.
- **Implications**: Automated load-testing scripts (e.g., Locust or k6) will be specified in the testing roadmap, and backend endpoints will be benchmarked under simulated multi-user load.

---

### DEC-014: Database Integrity Constraints, Immutability, and Result Release Architecture
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - **Student Assignment Identity**: `QuizAssignment` enforces unique constraints on both `(quiz_id, student_prn)` and `(quiz_id, student_email)` to prevent duplicate roster rows and email collision. When mapping an authenticated user (`users.id`) to a quiz assignment, both verified email and PRN must match. Any mismatch requires administrative/teacher review and must never grant unauthorized attempt access.
  - **Published Version Immutability**: `quiz_versions.quiz_id` foreign key enforces `ON DELETE RESTRICT` rather than cascading deletes. Quizzes with published versions or historical attempts cannot be hard deleted; they must be archived (`is_archived = true`). An explicit `is_published` boolean distinguishes draft versions from immutable published snapshots.
  - **Scoring & Result-Release Consistency**: `QuizVersion.is_results_released` (along with `results_released_at` and `results_released_by_id`) serves as the sole authoritative visibility gate for student score and answer inspection. `QuizAttempt.grading_status` is an internal scoring lifecycle/audit status with values `pending`, `auto_graded`, and `manually_adjusted`. No student-facing API endpoint may present individual or overall scores as released when the parent `QuizVersion.is_results_released` is false.
  - **Scoring & Configuration Constraints**: Database `CheckConstraint`s enforce:
    - Questions: `positive_marks > 0` and `negative_marks >= 0`.
    - Quiz Versions: `duration_minutes > 0`, `max_attempts > 0`, `closes_at > opens_at`, `tab_switch_limit >= 0`, `tab_switch_penalty_marks >= 0`.
    - Quiz Attempts: `attempt_number >= 1`, `deadline_at >= started_at`, `tab_switch_count >= 0`.
    - Multi-Answer Policy: `QuizVersion.multi_answer_policy` configuration explicitly records the scoring policy: `all_or_nothing`, `partial_with_penalty`, or `partial_no_penalty`.
  - **Application-Level Validation Rules**: Database constraints are complemented by strict application-level validation: verifying at least 2 options per question, at least 1 correct option before publishing, exactly 1 correct option for single-choice questions, and enforcing attempt deadlines as $\min(\text{started\_at} + \text{duration}, \text{closes\_at})$.
- **Rationale**: Guarantees relational defense-in-depth against accidental data deletion, prevents assignment hijacking, and eliminates semantic ambiguity between internal grading lifecycle and student result visibility.
- **Implications**: Schema changes are captured in Alembic migration `0002_integrity` and validated via automated metadata tests and offline SQL generation.

---

### DEC-015: Authentication Integration Readiness & Non-Self-Promoting User Provisioning
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - **Explicit Algorithm Enforcement**: Token verification explicitly verifies the configured algorithm (`settings.SUPABASE_JWT_ALGORITHM`, default `HS256`). For symmetric projects, `SUPABASE_JWT_SECRET` is used; for asymmetric projects (`RS256`, `ES256`), `SUPABASE_JWT_PUBLIC_KEY` is supported. Under no circumstances will the system accept `none` or arbitrary client-asserted algorithms.
  - **User Provisioning & Role Safety**:
    - Self-registration via the public Supabase Auth flow is restricted to `UserRole.STUDENT`. The client cannot specify, request, or manipulate their role.
    - `teacher` and `admin` roles can never be self-selected. They must be provisioned through out-of-band administrative action (e.g., initial seed scripts, institutional directory sync, or admin portal provisioning).
    - Authorization checks always query the application database `users.role`. JWT claims (e.g. `role`, `user_metadata`, `app_metadata`) and request body roles are strictly untrusted for authorization.
  - **Secret Separation**:
    - Frontend public config: `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.
    - Backend-only private secrets: `DATABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`. Service role keys and JWT secrets must never be exposed to the browser or client bundle.
  - **Prerequisites for Live Integration**:
    - Required: `DATABASE_URL` (backend), `SUPABASE_JWT_SECRET` (backend), `VITE_SUPABASE_URL` (frontend), `VITE_SUPABASE_ANON_KEY` (frontend).
    - Optional: `SUPABASE_SERVICE_ROLE_KEY` (for administrative user management), `SUPABASE_JWT_ISSUER`, `SUPABASE_JWT_AUDIENCE`.
- **Rationale**: Prevents privilege escalation and credential leakage while establishing a clear, auditable boundary between Supabase identity and Quizdesk authorization.
- **Implications**: Frontend client and backend services adhere strictly to separate environment files (`frontend/.env.local` vs. `backend/.env`).

---

### DEC-016: Question Difficulty Classification and Dual-Format Spreadsheet Ingestion (.CSV and .XLSX)
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - **Constrained Difficulty Enum**: Added a database-level `QuestionDifficulty` enum with values `easy`, `medium`, and `hard`. Enforced via SQL check constraint (`ck_question_difficulty_enum`) and an index (`ix_questions_difficulty`) for fast faceted querying.
  - **Safe Historical Migration & Server Default**: Existing and imported questions without explicit difficulty default safely to `'medium'` at both database and application layers, avoiding null pointer issues while accurately representing typical assessment baselines.
  - **Scoring Neutrality**: Question difficulty is purely an analytical and organizational facet; it has zero implicit impact on positive or negative marks.
  - **Dual Spreadsheet Ingestion**:
    - Both standard `.csv` (with UTF-8 and UTF-8-BOM support) and genuine `.xlsx` (via `openpyxl`) workbooks are accepted.
    - Automatic format detection via file extension and MIME type.
    - Size and count limits: 2MB file limit and 200 question row limit to protect memory and CPU.
    - Normalization: Difficulty inputs are trimmed and lowercased; unrecognized difficulty values produce actionable row-level validation errors rather than silently coercing or crashing.
- **Rationale**: Eliminates format friction for teachers who draft questions in Microsoft Excel while guaranteeing robust validation, predictable scoring, and relational integrity.
- **Implications**: Pinned `openpyxl==3.1.5` in backend dependencies; updated Alembic migration `0004_question_difficulty.py` with backward-compatible defaults.

---

### DEC-017: Teacher Quiz Builder, Question Cloning Isolation, and Immutable Version Lifecycle
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - **Question Bank Isolation via Deep Copy**: When questions from the reusable question bank are added to a quiz, they are deep-copied into new `Question` records linked directly to the draft `quiz_version_id`. Modifying, deleting, or re-importing questions in the bank will never alter existing quiz drafts or published assessment content.
  - **Immutable Version Locking**:
    - Publishing a quiz transitions the active `QuizVersion.is_published` from `false` to `true` inside a single atomic database transaction.
    - Pre-publication server validation strictly verifies:
      - At least 1 question is attached.
      - Every attached question has at least 2 options and at least 1 correct answer.
      - Assessment schedule is valid (`closes_at > opens_at`).
      - Assessment duration is positive (`duration_minutes > 0`).
      - Maximum attempts is positive (`max_attempts > 0`).
  - **Version Forking on Subsequent Draft Edits**:
    - Once a `QuizVersion` is published, any subsequent configuration edit, question addition, question removal, or reordering request automatically branches a new draft `QuizVersion` (incrementing `version_number`), deep-cloning all settings, questions, and options.
    - Existing student attempts, answers, and telemetry remain permanently attached to the specific `QuizVersion` they began on.
  - **Cross-Teacher Isolation**:
    - Endpoints under `/api/v1/quizzes` verify ownership against the authenticated teacher (`quiz.created_by_id == current_user.id`). Attempting to view or mutate another teacher's quiz returns a safe HTTP 404 Not Found to prevent metadata probing.
- **Rationale**: Guarantees total academic integrity and stability during live simultaneous exams; prevents teachers from inadvertently modifying tests while students are actively sitting for them.
- **Implications**: Quizzes maintain a clean lineage of versioned snapshots; attempt grading evaluates against the exact frozen version snapshot.

---

### DEC-018: Student Roster Ingestion, Identity Alignment, and Server-Authoritative Eligibility
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - **Roster Ingestion vs. User Identity**: Uploading a student roster CSV or Excel workbook (`prn,name,email,division`) creates eligibility records (`QuizAssignment`), but never creates user accounts, authenticates users, or elevates permissions. Roster uploads are strictly identity assertions, not proof of identity.
  - **Dual Identifier Verification (Email + PRN)**:
    - A student account is bound to an assignment (`assigned_student_id`) only when both the verified account email AND registered profile PRN match the roster row.
    - If email matches but PRN differs, or if PRN belongs to another user, an Identity Conflict is raised and the assignment remains unlinked/blocked pending administrative review.
    - If no user account exists yet, the assignment is created in an `unregistered` state (`assigned_student_id = NULL`), ready for automated linkage when the student completes registration.
  - **Additive Import Default**:
    - Re-importing a roster or importing subsequent batches is additive by default; students omitted from a later file are never silently revoked or deleted.
    - Existing assignments have their name/division updated idempotently without generating duplicate rows or corrupting assignment primary keys.
  - **Assignment Lifecycle & Attempt Protection**:
    - `QuizAssignment` supports `is_active`, `revoked_at`, and `revoked_by_id`.
    - Hard deletion of an assignment is permitted only if the student has no historical attempts on that quiz. If attempts exist, hard deletion is blocked with HTTP 400 Bad Request, requiring revocation instead to safeguard attempt audit trails.
    - All roster imports, additions, status toggles, and deletions record tamper-evident `AuditEvent`s.
  - **Server-Authoritative Eligibility Gate**:
    - Student attempt endpoints verify eligibility strictly on the server: checking active account status, published quiz status, active assignment presence, verified identity alignment, and assessment scheduling windows (`opens_at <= now <= closes_at`).
- **Rationale**: Prevents identity spoofing, protects historical assessment attempts, and guarantees reliable eligibility enforcement under concurrent exam conditions.
- **Implications**: Migration `0005_assignment_lifecycle.py` introduced assignment status tracking; endpoint `GET /api/v1/student/quizzes/{id}/eligibility` exposes sanitized eligibility status without leaking exam contents.

---

### DEC-019: Secure Student Assessment Engine, Shuffling Persistence, Autosave Invariants, and Authoritative Grading
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - **Server-Authoritative Attempt Lifecycle**:
    - An attempt session (`QuizAttempt`) is created only after authoritative verification of student role, active account status, active assignment, and scheduled availability window (`opens_at <= now <= closes_at`).
    - Attempt deadline is strictly computed as $\min(\text{started\_at} + \text{duration\_minutes}, \text{closes\_at})$.
    - Idempotent Resumption: Repeated start requests or page refreshes return the existing active in-progress attempt without creating duplicate attempts or resetting deadlines.
    - Attempt Limits: Bounded strictly by `QuizVersion.max_attempts` backed by database unique constraints (`uq_attempt_number_per_student`).
  - **Randomized Sequence Persistence**:
    - When `shuffle_questions` or `shuffle_options` is enabled on the `QuizVersion`, randomized sequences are permanently stored in `QuizAttempt.question_order` (JSON array of question IDs) and `QuizAttempt.option_order` (JSON dict of `{question_id: [option_ids]}`).
    - Every retrieval, refresh, and autosave interaction strictly references the persisted order, preventing option permutation errors across reconnects.
  - **Concealed Delivery Payloads**:
    - Assessment delivery endpoints (`GET /api/v1/student/attempts/{id}`) serialize through dedicated `SanitizedQuestionResponse` and `SanitizedOptionResponse` Pydantic models.
    - Fields such as `is_correct`, `explanation`, or correct answer keys are strictly omitted from active assessment schemas.
  - **Autosave Invariants & Out-of-Order Write Defense**:
    - Autosaves (`PUT /api/v1/student/attempts/{id}/answers/{question_id}`) update targeted `AttemptAnswer` rows without reloading the full quiz.
    - Out-of-order delayed HTTP writes are safely rejected by comparing monotonic `client_timestamp` against existing saved timestamps.
    - Saves attempted after the authoritative server deadline or after attempt finalization are rejected with HTTP 409 Conflict.
  - **Authoritative Grading & Result Release Isolation**:
    - All grading evaluates on the server in `finalize_and_grade_attempt` across single-choice, True/False, and multi-answer policies (`all_or_nothing`, `partial_no_penalty`, `partial_with_penalty`).
    - Tab switch penalty deductions are evaluated transactionally.
    - Final scores and correctness breakdowns remain concealed from students until the instructor explicitly triggers result release (`QuizVersion.is_results_released == True`).
- **Rationale**: Eliminates client-side exam tampering, prevents timer and attempt count exploitation, protects student work against flaky connections, and guarantees academic integrity.
- **Implications**: Schema updated in migration `0006_attempt_shuffling.py`; student endpoints mounted under `/api/v1/student/`.

---

### DEC-020: Teacher Results Management, Score Adjustments, Controlled Release, and CSV Export
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - **Teacher Assessment Result Diagnostics**:
    - Teachers can query aggregate KPI score statistics (class average, highest score, lowest score, submitted count, in-progress count) calculated strictly on the server using bounded queries.
    - Attempt tables support pagination (max 100 items per page), lifecycle status filtering, and multi-field text search across student PRN, name, and email.
    - Detail views grant teachers full transparency: question responses, option correctness flags (`is_correct`), awarded marks, telemetry logs (window blurs / tab switches), and adjustment histories.
  - **Authoritative Manual Grade Adjustments with Immutable Audit Trail**:
    - Score adjustments (`POST /api/v1/quizzes/{id}/results/attempts/{attempt_id}/adjust`) require a non-blank justification reason (min 3 characters).
    - Permitted only for finalized attempts (`is_finalized == True` or status in `submitted`, `expired`); in-progress attempts cannot be manually adjusted.
    - Score validation: finite, non-negative, and bounded by maximum possible assessment marks ($0 \le \text{new\_score} \le \text{max\_marks}$).
    - Preserves previous score and full revision history in `grade_adjustments` table; updates `QuizAttempt.grading_status` to `manually_adjusted`.
    - Generates tamper-resistant `AuditEvent` with action `grade_manually_adjusted`.
    - Safe to retry: identical scores return the current attempt state without duplicating adjustment entries.
  - **Controlled Result Release Gate**:
    - Result release (`POST /api/v1/quizzes/{id}/results/release`) is an explicit, authorized teacher action operating on the active published `QuizVersion` (`is_results_released = True`, `results_released_at = utc_now()`).
    - Idempotent: repeated release requests return confirmation without mutating timestamps or generating redundant audit entries.
    - Prior to release: student score inquiries (`GET /api/v1/student/attempts/{id}/result`) return HTTP 403 Forbidden with details withheld.
    - Following release: students can view only their personal total score, grading status, and completion summary; answer keys and other students' marks remain concealed.
  - **CSV Export & Formula Injection Sanitization**:
    - Teacher-only CSV export (`GET /api/v1/quizzes/{id}/results/export`) streams results in a documented 12-column structure: `PRN, Student Name, Student Email, Division, Attempt Number, Status, Started At (UTC), Submitted At (UTC), Score, Max Marks, Grading Status, Tab Switches`.
    - All text cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r` are sanitized by prepending a single quote (`'`), neutralizing spreadsheet formula execution exploits (CSV Injection / CWE-1236).
    - Empty assessments return standard headers without error.
- **Rationale**: Ensures complete institutional accountability for post-exam score modifications, guarantees privacy and security for student cohorts, and delivers clean academic reporting.
- **Implications**: Leverages existing `grade_adjustments`, `audit_events`, and `quiz_versions` tables without requiring schema migrations; endpoints mounted under `/api/v1/quizzes/{id}/results`.

---

### DEC-021: Assessment Proctoring Hardening, Configurable Penalties & Audit Diagnostics
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - **Granular Teacher-Configurable Proctoring Policy & Sensible Defaults**:
    - Each assessment version snapshot specifies:
      - `tab_switch_limit` (free violation allowance, default 2, min 0).
      - `tab_switch_penalty_marks` (deduction per violation, default 1.0, supports half-marks e.g. 0.5).
      - `max_proctoring_deduction` (cumulative penalty cap, default 5.0).
      - `enable_copy_paste_restriction` (default true) & `count_copy_paste_violations` (default true).
      - `require_fullscreen` (default true) & `count_fullscreen_exit_violations` (default true).
      - `count_tab_switch_violations` (default true).
      - `count_dev_tools_violations` (default true).
      - `enable_proctoring_warnings` (default true).
    - Existing quizzes and immutable published versions retain their established settings and historical behavior.
  - **Authoritative & Bounded Penalty Scoring Formula**:
    - Calculated as:
      $$\text{chargeable\_violations} = \max(0, V - F)$$
      $$\text{proctoring\_deduction} = \min(\text{chargeable\_violations} \times D, C, \max(0, S))$$
      $$\text{final\_score} = \max(0, S - \text{proctoring\_deduction})$$
    - Stored independently on `QuizAttempt.proctoring_deduction` and `QuizAttempt.violation_count`.
    - Never reduces final scores below zero, never exceeds configured cumulative cap $C$, and never exceeds student's available earned score $S$.
    - Deductions are applied exactly once during finalization and persist consistently across recalculations, reviews, and retries.
  - **Hardened Server-Authoritative Telemetry Invariants**:
    - Every telemetry event accepts an optional idempotent `client_event_id` (indexed in `attempt_telemetry_events`), preventing retry duplication.
    - Paired browser visibility and blur events (e.g., rapid Alt+Tab firing both `window_blur` and `tab_switch`) are deduplicated within a 1.0-second sliding window.
    - Rate-limiting prevents event flooding (max 1 event per 1.5 seconds from client per event type).
    - Only valid, policy-supported event types contribute to chargeable violations (`tab_switch`, `window_blur`, `fullscreen_exit`, `copy_paste_attempt`, `dev_tools_shortcut`).
    - Rejection of invalid, unsupported, or deceptive event types (e.g. fake screenshot signals). No unsubstantiated claims of OS-level screenshot detection or universal AI assistant identification.
  - **Pre-Quiz Assessment Readiness Screen**:
    - Student must review full proctoring rules, navigation rules, time limit, and penalty calculation breakdown before beginning attempt.
    - Automated client-side capability checks verify browser environment, Fullscreen API support, and server connectivity.
    - Fullscreen is requested in direct response to user confirmation click, adhering to strict browser user-gesture requirements.
  - **Transparent In-Assessment Violation UX**:
    - Scoped deterrents prevent clipboard copying, cutting, pasting, and context menu within the assessment container.
    - Fullscreen exit listeners trigger a persistent top banner prompting immediate return to fullscreen.
    - Compact, non-intrusive live violation indicator displays accepted count, remaining free quota, and cumulative score deduction.
  - **Teacher Results Telemetry Diagnostics**:
    - Teacher attempt detail modal presents violation breakdown by event category, effective policy snapshot, and timestamped event history.
- **Rationale**: Replaces hardcoded tab-switch rules with teacher-configurable academic integrity policies; provides complete fairness and auditability while preventing browser-based student cheating.
- **Implications**: Schema updated in migration `0007_proctoring_hardening.py` adding check constraints and proctoring columns on `quiz_versions`, `quiz_attempts`, and `attempt_telemetry_events`.

---

### DEC-022: Restricted Operational Admin Portal, Guarded Test Reset, Teacher Password Recovery & Roster Verification
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - **Separate Portal Entry Points & Role-Aware Navigation**:
    - Dedicated entry points for student (`/student/login`), teacher (`/teacher/login`), and admin (`/admin/login`).
    - Student portal and navigation shell never display admin links, controls, or indicators.
    - All admin API routes (`/api/v1/admin/*`) enforce backend role checks via `require_admin` dependency; client route guards are supplementary UX only.
  - **Single Administrator Provisioning**:
    - Designated administrator identity configured via environment variables (`ADMIN_EMAIL`, `ADMIN_NAME`, `ADMIN_BOOTSTRAP_TOKEN`), never hardcoded in code, database seeds, or client bundles.
    - Provisioning endpoint `POST /api/v1/admin/bootstrap` decodes verified Supabase JWT; assigns `UserRole.ADMIN` only if token email matches `ADMIN_EMAIL` and provided bootstrap token matches `ADMIN_BOOTSTRAP_TOKEN`.
    - No client-supplied roles, metadata, or public signup requests can ever grant administrative privileges.
  - **Minimal Admin Dashboard**:
    - Bounded, efficient KPI metrics: total registered students, total teachers, total quizzes, published quizzes, active attempts, and total attempts.
    - Paginated user directory with text search across name, email, and student PRN; allows toggling account activation status while strictly blocking administrator self-deactivation.
    - Paginated audit trail viewer with action filtering and JSON details inspection.
  - **Guarded Destructive Test-Data Reset Utility**:
    - Exclusively intended as a non-production development/testing utility.
    - High-integrity safeguards:
      1. Disabled by default (`ALLOW_DESTRUCTIVE_RESET=false`).
      2. Strictly blocked when `ENVIRONMENT=production` (returns HTTP 403 Forbidden).
      3. Requires authenticated admin role.
      4. Requires explicit request confirmation code matching `CONFIRM_DELETE_ALL_TEST_DATA` (returns HTTP 400 Bad Request otherwise).
      5. Strictly transactional deletion in foreign-key dependency order: `attempt_answers` $\rightarrow$ `attempt_telemetry_events` $\rightarrow$ `grade_adjustments` $\rightarrow$ `quiz_attempts` $\rightarrow$ `quiz_assignments` $\rightarrow$ `import_jobs` $\rightarrow$ `question_options` $\rightarrow$ `questions` $\rightarrow$ `quiz_versions` $\rightarrow$ `quizzes`.
      6. Preserves all user authentication accounts (including Administrator) and preserves the tamper-evident `audit_events` log.
      7. Records a `system.destructive_reset` audit event detailing cleared record counts and operator identity.
  - **Teacher Password Recovery**:
    - Built on standard Supabase Auth recovery workflow (`supabase.auth.resetPasswordForEmail` $\rightarrow$ `/teacher/reset-password` $\rightarrow$ `supabase.auth.updateUser`).
    - Uses generic success responses to mitigate user enumeration risks.
    - Secrets kept on the server; public client config uses `.env.local` / `.env.example` templates.
  - **Roster Cross-Teacher Enrollment & Assignment Integrity**:
    - Roster assignments are strictly scoped per assessment (`quiz_assignments.quiz_id`).
    - Cross-teacher enrollment is non-conflicting: Teacher A assigning student X to Quiz A does not conflict with Teacher B assigning student X to Quiz B.
    - Same-quiz duplicate assignments are prevented at database (`uq_quiz_assignment_prn`, `uq_quiz_assignment_email`) and service levels; re-imports are idempotent.
    - PRNs are preserved as strings with leading zeros intact.
    - PRN/email mismatches are detected as identity conflicts and rejected with HTTP 422 Unprocessable Entity.
- **Rationale**: Delivers required operational oversight and test agility while preserving rigorous security boundaries, credential hygiene, and academic data integrity.
- **Implications**: Endpoints implemented in `backend/app/api/v1/endpoints/admin.py`, services in `backend/app/services/admin_service.py`, frontend routes in `frontend/src/pages/admin/` and `frontend/src/pages/auth/`. Verified by 154 automated backend tests and frontend build.

---

### DEC-023: Production Hosting Architecture & Container Packaging (Vercel + Hugging Face Spaces + Supabase)
- **Status**: `Confirmed`
- **Date**: 2026-10-23
- **Decision**:
  - **Frontend Hosting (Vercel)**:
    - Deployed as a static single-page application (SPA) from the `frontend/` directory using Vite build output (`dist`).
    - Client-side React Router rewrites configured via `frontend/vercel.json` (`"rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]`).
    - Environment variables limited strictly to public client properties: `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.
    - Plan considerations: Vercel Hobby tier is suitable for proof-of-concept and academic evaluation. For institutional pilots requiring formal compliance or shared team collaboration, Vercel Pro or zero-cost Cloudflare Pages are designated fallback alternatives.
  - **Backend Hosting (Hugging Face Spaces - Docker)**:
    - Packaged via production Docker container with Python 3.12 slim base.
    - Hugging Face Spaces port requirement: listens on internal default port `7860` (`EXPOSE 7860`, `CMD ... --port ${PORT:-7860}`) while maintaining dynamic `$PORT` compatibility.
    - Hugging Face Spaces permission requirement: runs under unprivileged non-root user `user` with `UID 1000`.
    - Lifecycle and cold start: Free tier provides 2 vCPUs and 16 GB RAM with a 48-hour inactivity sleep timeout. Cold boot takes ~15–30s. Background keep-alive pingers are strictly prohibited. Instead, the operational procedure mandates pre-warming the backend 10–15 minutes before scheduled exam windows to ensure zero student disruption.
    - Secrets management: All sensitive backend credentials (`DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `ADMIN_BOOTSTRAP_TOKEN`, `ENVIRONMENT=production`) are configured through the Hugging Face Space Settings "Variables and secrets" vault.
  - **Database & Authentication (Supabase)**:
    - Retains existing Supabase project for PostgreSQL 17 and Supabase Auth.
    - Connected via Supabase Session Pooler (port 5432) with calibrated bounds (`DB_POOL_SIZE=8`, `DB_MAX_OVERFLOW=4`) to honor free-tier connection limits while servicing 30+ concurrent students.
    - Production CORS origins and Supabase Auth redirect URLs explicitly configured with the assigned Vercel production domain.
    - Database state verified: 0 active test users, 0 test quizzes, 0 test attempts, and 244 immutable audit records retained.
- **Rationale**: Provides a zero-cost, high-reliability deployment stack with ample compute (2 vCPUs, 16 GB RAM), reasonable inactivity windows (48 hours), fast static global CDN distribution, and strict secret isolation.
- **Implications**: Container configuration updated in `backend/Dockerfile`, Pydantic Settings updated for path resolution, hardcoded URLs eliminated in frontend pages, and deployment runbook documented in `docs/OPERATIONS_RUNBOOK.md`.
