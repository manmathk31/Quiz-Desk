# AGENTS.md - Repository Rules and Instructions for AI Coding Assistants

This repository contains **Quizdesk**, an institutional assessment and college quiz platform designed for high reliability, strict academic integrity, and seamless student/teacher workflows.

All AI coding assistants (including Antigravity, Claude, ChatGPT, Copilot, etc.) working on this repository **MUST** strictly adhere to the following 13 foundational operating rules and guidelines before proposing or making any changes.

---

## 1. Mandatory Pre-Flight Reading
Before analyzing, proposing, or editing any code or documentation, read the following core project documents located in the repository:
- [`AGENTS.md`](file:///d:/ANUP/Quizdesk/AGENTS.md) (This file)
- [`docs/PROJECT_LOG.md`](file:///d:/ANUP/Quizdesk/docs/PROJECT_LOG.md) (Current stage, system status, execution logs, and next steps)
- [`docs/DECISIONS.md`](file:///d:/ANUP/Quizdesk/docs/DECISIONS.md) (Authoritative architectural decision records)
- [`docs/TASK_TRACKER.md`](file:///d:/ANUP/Quizdesk/docs/TASK_TRACKER.md) (Current task statuses, dependencies, and acceptance criteria)
- [`docs/ARCHITECTURE.md`](file:///d:/ANUP/Quizdesk/docs/ARCHITECTURE.md) (System architecture, security boundaries, and data flow)

## 2. Decision Authority
Treat all decisions marked as `Confirmed` in [`docs/DECISIONS.md`](file:///d:/ANUP/Quizdesk/docs/DECISIONS.md) as strictly binding and authoritative.
- Never silently overturn, bypass, or alter a confirmed decision.
- If technical realities or requirements demand a deviation, explicitly state the conflict, describe the trade-offs, and request user approval before proceeding.

## 3. Strict Single-Task Focus
Work on **one clearly scoped, atomic task at a time**.
- Do not combine multiple roadmap milestones into a single prompt execution.
- Maintain a focused diff that can be reviewed, verified, and rolled back independently if necessary.

## 4. Inspect Before Editing
Always inspect existing files, project configurations, directory layouts, and dependencies before attempting edits.
- Never assume an API, component, module, or schema exists without reading its definition.
- Verify file locations and syntax prior to applying modifications.

## 5. Specification and Acceptance Criteria First
Before executing substantial implementations:
- Present a concise summary of the planned changes.
- Define explicit acceptance criteria and verification steps.
- Ensure alignment with existing architectural boundaries before writing code.

## 6. Anti-Bloat & Pragmatic Engineering
Adhere to clean, maintainable engineering:
- Avoid unrelated refactoring of working code.
- Avoid unnecessary external dependencies and heavy libraries when simple, standard implementations suffice.
- Avoid premature abstractions, speculative features, or over-engineered design patterns.
- Build strictly to current confirmed requirements.

## 7. Verification Over Assumption
Never claim that a build, test, command, or feature succeeded unless it was actually executed and the output was inspected.
- If a test or command fails, report the actual failure and diagnostic output truthfully.
- Provide reproducible steps or command invocations for verification.

## 8. Continuous Documentation Sync
At the conclusion of every task, update the relevant project documentation:
- Record new decisions in [`docs/DECISIONS.md`](file:///d:/ANUP/Quizdesk/docs/DECISIONS.md).
- Update task progress and acceptance criteria in [`docs/TASK_TRACKER.md`](file:///d:/ANUP/Quizdesk/docs/TASK_TRACKER.md).
- Record actions, commands run, test results, files modified, and next recommended tasks in [`docs/PROJECT_LOG.md`](file:///d:/ANUP/Quizdesk/docs/PROJECT_LOG.md).
- Update [`docs/ARCHITECTURE.md`](file:///d:/ANUP/Quizdesk/docs/ARCHITECTURE.md) if structural patterns or security boundaries change.

## 9. Secret & Credential Zero-Tolerance
Never store, log, or commit sensitive credentials:
- Passwords, API secret keys, JWT secrets, database connection URIs with credentials, Supabase service-role keys, and private tokens must never appear in documentation, git commits, log output, or client-side frontend code.
- Always use environment variables (`.env.example` templates with empty placeholders) and secure server-side secret management.

## 10. Explicit Confirmation for Destructive & Consequential Actions
Request explicit user clarification and approval before:
- Deleting or overwriting existing user data, files, or database tables.
- Modifying confirmed database migrations or foundational schema structures.
- Running operations that irreversibly alter external services or repository history.

## 11. Preserving Persistent Project Memory
Never overwrite or truncate [`docs/PROJECT_LOG.md`](file:///d:/ANUP/Quizdesk/docs/PROJECT_LOG.md) into a high-level summary that discards past technical decisions, failed experiments, or rationale.
- Append new dated entries and keep existing history intact.
- Separate confirmed facts from tentative proposals or unresolved questions.

## 12. Repo-Truth Alignment
Ensure that documentation and code state reflect the true reality of the repository:
- Do not refer to packages or directories as present until they are actually created and verified.
- Keep file paths, configuration variables, and status indicators synchronized with the actual filesystem.

## 13. Disciplined Git Workflow & Conventional Commits
Maintain a clean, traceable, and secure Git history:
- Make small, focused Git commits after each logically complete, verified unit of work.
- Use short, descriptive conventional commit messages, for example:
  - `chore: scaffold frontend`
  - `chore: configure backend`
  - `feat: add student login`
  - `feat: implement quiz creation`
  - `fix: prevent duplicate submissions`
  - `test: cover quiz expiry`
  - `docs: update setup guide`
- Run relevant checks before committing and inspect the staged diff.
- Never commit secrets, credentials, local environment files, virtual environments, or generated dependencies.
- Never rewrite shared history or run destructive Git commands without explicit approval.
- Do not make empty commits or bundle unrelated work together.
- Update the project log and task tracker as appropriate, then include documentation updates in the relevant focused commit.
- Do not claim a commit succeeded unless you verify the resulting Git state and commit hash.

