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
  - Staged diff verified to ensure zero secrets or unintended files are present.
  - Executed initial commit with message: `chore: establish project baseline`.

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

---

## 6. Dependencies Added / Removed
- None. (Zero external packages installed in this setup task, adhering strictly to scope).

---

## 7. Tests Performed & Actual Results
- **Filesystem & Git Verification**:
  - Verified presence of all 5 baseline documents and `.gitignore`.
  - Verified `.gitignore` ignore and un-ignore logic via `git check-ignore`.
  - Staged diff inspection before commit.

---

## 8. Known Issues, Risks & Unresolved Questions

### Known Risks:
1. **Synchronized Peak Concurrency**: In collegiate assessments, hundreds of students concurrently open questions and autosave answers at the exact same minute. Mitigated by DEC-001, DEC-002, and DEC-013 with planned load simulation (Locust/k6) and connection pooling.
2. **Client Clock Drift / Manipulation**: Students attempting to manipulate local system time to gain exam minutes. Mitigated by DEC-008 and DEC-009 where server timestamps are strictly authoritative.
3. **Tab-Switch Telemetry False Positives**: Browser window blur events can be triggered by system notifications or accidental trackpad gestures. Mitigated by DEC-009 specifying tab-switch events as telemetry context rather than automated immediate failure.

### Unresolved Questions / Future Confirmations:
- Exact Supabase project URL and keys to be configured via `.env` in Phase 2.
- Institutional CSV schema variations (e.g., whether student names include middle names or prefixes; handled via robust string normalization).

---

## 9. Deviations from Agreed Decisions
- **None**: All actions strictly complied with Phase 1 boundary constraints and confirmed decisions.

---

## 10. Recommended Next Task

**Task**: **`TASK-102`: Python virtual environment & backend scaffolding**
- Create dedicated Python virtual environment `.venv/`.
- Initialize backend project layout with `pyproject.toml` (or `requirements.txt`) pinning FastAPI, Pydantic, SQLAlchemy, Alembic, and test tools.
- Implement baseline health check endpoint (`GET /health`) and verify with `pytest`.

