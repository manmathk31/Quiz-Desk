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

