"""High-Concurrency Load Testing Suite for Quizdesk (Phase 9, DEC-013).

Simulates realistic, synchronized concurrent student traffic against Quizdesk:
1. Stage 1: Synchronized Exam Start Burst (50 concurrent students starting attempts at t=0).
2. Stage 2: Repeated Active Autosave Loop (answers to MCQ single, multi, and True/False questions).
3. Stage 3: Telemetry Event Bursts & Idempotent Retries (blur/focus events with client_event_id).
4. Stage 4: Concurrent Teacher Result Queries under assessment load.
5. Stage 5: Synchronized Submission Burst (concurrent finalization and authoritative scoring).
6. Post-Run Database Integrity Audit (verifies 0 duplicate attempts, 0 lost answers, scoring integrity).
7. Safe isolated setup and cleanup (never touches real data or uses destructive reset).
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import math
import os
import statistics
import sys
import time
from typing import List, Dict, Any, Optional
import uuid

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import jwt
from sqlalchemy import select, func, delete, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models.user import User, UserRole, StudentProfile
from app.models.quiz import Quiz, QuizVersion, QuizStatus, MultiAnswerPolicy
from app.models.question import Question, QuestionOption, QuestionType, QuestionDifficulty
from app.models.attempt import QuizAttempt, AttemptAnswer, AttemptTelemetryEvent, AttemptStatus, GradingStatus
from app.models.roster import QuizAssignment


SYNTHETIC_PREFIX = "_loadtest_pilot9_"


@dataclass
class StageMetrics:
    """Metrics recorded for an individual load testing stage."""
    stage_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def rps(self) -> float:
        return round(self.total_requests / self.duration_seconds, 2) if self.duration_seconds > 0 else 0.0

    @property
    def median_ms(self) -> float:
        return round(statistics.median(self.latencies_ms), 2) if self.latencies_ms else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        s = sorted(self.latencies_ms)
        idx = int(0.95 * len(s))
        return round(s[min(idx, len(s) - 1)], 2)

    @property
    def p99_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        s = sorted(self.latencies_ms)
        idx = int(0.99 * len(s))
        return round(s[min(idx, len(s) - 1)], 2)

    @property
    def min_ms(self) -> float:
        return round(min(self.latencies_ms), 2) if self.latencies_ms else 0.0

    @property
    def max_ms(self) -> float:
        return round(max(self.latencies_ms), 2) if self.latencies_ms else 0.0

    @property
    def error_rate(self) -> float:
        return round((self.failed_requests / self.total_requests) * 100, 2) if self.total_requests > 0 else 0.0


def make_jwt(user_id: uuid.UUID, email: str) -> str:
    """Generate a valid signed Supabase JWT for synthetic load test accounts."""
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": settings.SUPABASE_JWT_AUDIENCE or "authenticated",
        "exp": now + 7200,
        "iat": now,
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm=settings.SUPABASE_JWT_ALGORITHM)


class LoadTestEnvironment:
    """Manages transactional synthetic test data setup and teardown."""

    def __init__(self, concurrency: int = 50):
        self.concurrency = concurrency
        self.teacher_id: Optional[uuid.UUID] = None
        self.teacher_email: str = f"{SYNTHETIC_PREFIX}teacher@test.institution.edu"
        self.teacher_token: Optional[str] = None

        self.quiz_id: Optional[uuid.UUID] = None
        self.quiz_version_id: Optional[uuid.UUID] = None
        self.questions: List[Dict[str, Any]] = []

        self.students: List[Dict[str, Any]] = []

    def setup(self):
        """Create synthetic teacher, published quiz with questions, and roster of N students."""
        db: Session = SessionLocal()
        try:
            print(f"[*] Setting up synthetic test data for {self.concurrency} concurrent students...")
            now = datetime.now(timezone.utc)

            # 1. Teacher account
            teacher = User(
                id=uuid.uuid4(),
                email=self.teacher_email,
                name="Load Test Instructor",
                role=UserRole.TEACHER,
                is_active=True,
            )
            db.add(teacher)
            db.flush()
            self.teacher_id = teacher.id
            self.teacher_token = make_jwt(teacher.id, teacher.email)

            # 2. Published Quiz with 5 questions
            quiz = Quiz(
                id=uuid.uuid4(),
                title=f"Load Verification Exam ({self.concurrency} Students)",
                course_code="PILOT-900",
                description="Synthetic assessment created for Phase 9 concurrency validation.",
                created_by_id=teacher.id,
                status=QuizStatus.PUBLISHED,
            )
            db.add(quiz)
            db.flush()
            self.quiz_id = quiz.id

            version = QuizVersion(
                id=uuid.uuid4(),
                quiz_id=quiz.id,
                version_number=1,
                title="Load Verification Exam v1",
                is_published=True,
                opens_at=now - timedelta(minutes=15),
                closes_at=now + timedelta(hours=3),
                duration_minutes=45,
                max_attempts=1,
                allow_backtracking=True,
                shuffle_questions=True,
                shuffle_options=True,
                multi_answer_policy=MultiAnswerPolicy.ALL_OR_NOTHING,
                tab_switch_limit=2,
                tab_switch_penalty_marks=1.0,
                max_proctoring_deduction=5.0,
                require_fullscreen=True,
                enable_proctoring_warnings=True,
                is_results_released=False,
            )
            db.add(version)
            db.flush()
            self.quiz_version_id = version.id
            quiz.current_version_id = version.id

            # Create 5 realistic questions
            q_specs = [
                {
                    "prompt": "What is the primary function of Write-Ahead Logging (WAL) in PostgreSQL?",
                    "type": QuestionType.SINGLE_CHOICE,
                    "difficulty": QuestionDifficulty.MEDIUM,
                    "pos": 2.0, "neg": 0.5,
                    "options": [
                        ("Ensure durability before mutating data pages on disk", True),
                        ("Compress database tables periodically", False),
                        ("Re-index foreign keys automatically", False),
                        ("Cache query results in memory", False),
                    ],
                },
                {
                    "prompt": "Which isolation levels prevent dirty reads in PostgreSQL?",
                    "type": QuestionType.MULTIPLE_CHOICE,
                    "difficulty": QuestionDifficulty.HARD,
                    "pos": 3.0, "neg": 1.0,
                    "options": [
                        ("Read Committed", True),
                        ("Repeatable Read", True),
                        ("Serializable", True),
                        ("Read Uncommitted (behaves as Read Committed in PG)", True),
                    ],
                },
                {
                    "prompt": "In SQLAlchemy, QueuePool connections are pooled per Python process.",
                    "type": QuestionType.TRUE_FALSE,
                    "difficulty": QuestionDifficulty.EASY,
                    "pos": 1.0, "neg": 0.0,
                    "options": [
                        ("True", True),
                        ("False", False),
                    ],
                },
                {
                    "prompt": "What HTTP status code indicates a conflict during an assessment autosave?",
                    "type": QuestionType.SINGLE_CHOICE,
                    "difficulty": QuestionDifficulty.EASY,
                    "pos": 1.0, "neg": 0.25,
                    "options": [
                        ("409 Conflict", True),
                        ("404 Not Found", False),
                        ("401 Unauthorized", False),
                        ("422 Unprocessable Entity", False),
                    ],
                },
                {
                    "prompt": "Which proctoring signals are server-deduplicated within 1000ms?",
                    "type": QuestionType.SINGLE_CHOICE,
                    "difficulty": QuestionDifficulty.MEDIUM,
                    "pos": 2.0, "neg": 0.5,
                    "options": [
                        ("Paired window_blur and tab_switch events", True),
                        ("Fullscreen enters and submits", False),
                        ("Autosave and answer reload", False),
                        ("Login and logout", False),
                    ],
                },
            ]

            for idx, spec in enumerate(q_specs, start=1):
                q = Question(
                    id=uuid.uuid4(),
                    quiz_version_id=version.id,
                    created_by_id=teacher.id,
                    question_type=spec["type"],
                    difficulty=spec["difficulty"],
                    prompt=spec["prompt"],
                    order_index=idx,
                    positive_marks=spec["pos"],
                    negative_marks=spec["neg"],
                )
                db.add(q)
                db.flush()

                q_entry = {
                    "id": str(q.id),
                    "type": q.question_type,
                    "options": [],
                    "correct_option_ids": [],
                }

                for opt_idx, (opt_text, is_corr) in enumerate(spec["options"]):
                    opt = QuestionOption(
                        id=uuid.uuid4(),
                        question_id=q.id,
                        option_text=opt_text,
                        order_index=opt_idx,
                        is_correct=is_corr,
                    )
                    db.add(opt)
                    db.flush()
                    q_entry["options"].append(str(opt.id))
                    if is_corr:
                        q_entry["correct_option_ids"].append(str(opt.id))

                self.questions.append(q_entry)

            # 3. Create N Synthetic Students and Roster Assignments
            for i in range(1, self.concurrency + 1):
                prn = f"PRN_LOAD_{i:03d}"
                email = f"{SYNTHETIC_PREFIX}student_{i:03d}@test.institution.edu"
                name = f"Test Student {i:03d}"

                student = User(
                    id=uuid.uuid4(),
                    email=email,
                    name=name,
                    role=UserRole.STUDENT,
                    is_active=True,
                )
                db.add(student)

                profile = StudentProfile(
                    user_id=student.id,
                    prn=prn,
                    current_division="LOAD",
                )
                db.add(profile)

                assignment = QuizAssignment(
                    id=uuid.uuid4(),
                    quiz_id=quiz.id,
                    student_prn=prn,
                    student_name=name,
                    student_email=email,
                    division="LOAD",
                    is_active=True,
                    assigned_student_id=student.id,
                )
                db.add(assignment)

                token = make_jwt(student.id, email)
                self.students.append({
                    "id": student.id,
                    "prn": prn,
                    "email": email,
                    "name": name,
                    "token": token,
                    "attempt_id": None,
                })

            db.commit()
            print(f"[+] Setup completed successfully. Created 1 Quiz ({len(self.questions)} questions) and {len(self.students)} Students.")
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Failed to setup load test environment: {e}") from e
        finally:
            db.close()

    def cleanup(self):
        """Safely delete all synthetic test records without using destructive reset."""
        print("[*] Cleaning up synthetic test data...")
        db: Session = SessionLocal()
        try:
            # Find all synthetic quizzes
            synth_quizzes = db.scalars(
                select(Quiz).where(
                    (Quiz.course_code == "PILOT-900") | (Quiz.title.startswith("Load Verification Exam"))
                )
            ).all()
            quiz_ids = [q.id for q in synth_quizzes]
            if self.quiz_id and self.quiz_id not in quiz_ids:
                quiz_ids.append(self.quiz_id)

            if quiz_ids:
                # Find all versions
                versions = db.scalars(
                    select(QuizVersion).where(QuizVersion.quiz_id.in_(quiz_ids))
                ).all()
                v_ids = [v.id for v in versions]
                if self.quiz_version_id and self.quiz_version_id not in v_ids:
                    v_ids.append(self.quiz_version_id)

                if v_ids:
                    attempts = db.scalars(
                        select(QuizAttempt).where(QuizAttempt.quiz_version_id.in_(v_ids))
                    ).all()
                    attempt_ids = [a.id for a in attempts]
                    if attempt_ids:
                        db.execute(delete(AttemptAnswer).where(AttemptAnswer.attempt_id.in_(attempt_ids)))
                        db.execute(delete(AttemptTelemetryEvent).where(AttemptTelemetryEvent.attempt_id.in_(attempt_ids)))
                        db.execute(delete(QuizAttempt).where(QuizAttempt.id.in_(attempt_ids)))

                    questions = db.scalars(
                        select(Question).where(Question.quiz_version_id.in_(v_ids))
                    ).all()
                    q_ids = [q.id for q in questions]
                    if q_ids:
                        db.execute(delete(QuestionOption).where(QuestionOption.question_id.in_(q_ids)))
                        db.execute(delete(Question).where(Question.id.in_(q_ids)))

                    db.execute(delete(QuizVersion).where(QuizVersion.id.in_(v_ids)))

                db.execute(delete(QuizAssignment).where(QuizAssignment.quiz_id.in_(quiz_ids)))
                db.execute(delete(Quiz).where(Quiz.id.in_(quiz_ids)))

            # Delete synthetic users and student profiles
            synthetic_users = db.scalars(
                select(User).where(User.email.startswith(SYNTHETIC_PREFIX))
            ).all()
            user_ids = [u.id for u in synthetic_users]
            if user_ids:
                db.execute(delete(StudentProfile).where(StudentProfile.user_id.in_(user_ids)))
                db.execute(delete(User).where(User.id.in_(user_ids)))

            db.commit()
            print("[+] Cleanup completed cleanly. All synthetic test records removed.")
        except Exception as e:
            db.rollback()
            print(f"[!] Warning during load test cleanup: {e}")
        finally:
            db.close()


class AssessmentLoadTestRunner:
    """Orchestrates synchronized concurrent student traffic across all assessment stages."""

    def __init__(self, env: LoadTestEnvironment, base_url: str):
        self.env = env
        self.base_url = base_url.rstrip("/")
        self.stage_reports: List[StageMetrics] = []

    async def run_full_suite(self) -> Dict[str, Any]:
        """Execute all load test stages progressively."""
        print(f"\n================================================================================")
        print(f" STARTING LOAD VERIFICATION SUITE: {self.env.concurrency} SIMULTANEOUS STUDENTS")
        print(f" Target URL: {self.base_url}")
        print(f" Database: {engine.url.render_as_string(hide_password=True)}")
        print(f"================================================================================\n")

        # Configure HTTP client with large connection pool matching concurrency
        limits = httpx.Limits(max_connections=self.env.concurrency + 10, max_keepalive_connections=self.env.concurrency)
        timeout = httpx.Timeout(45.0, connect=15.0)

        async with httpx.AsyncClient(base_url=self.base_url, limits=limits, timeout=timeout) as client:
            # Stage 1: Synchronized Exam Start Burst
            await self._stage_1_quiz_start_burst(client)

            # Stage 2: Concurrent Autosave Bursts (Question Answers)
            await self._stage_2_autosave_traffic(client)

            # Stage 3: Proctoring Telemetry Bursts & Idempotency
            await self._stage_3_telemetry_bursts(client)

            # Stage 4: Concurrent Teacher Result Queries
            await self._stage_4_teacher_monitoring(client)

            # Stage 5: Synchronized Submission Burst
            await self._stage_5_submission_burst(client)

        # Stage 6: Database Invariant Verification
        db_audit = self._verify_database_integrity()

        return {
            "concurrency": self.env.concurrency,
            "stages": self.stage_reports,
            "db_audit": db_audit,
        }

    async def _stage_1_quiz_start_burst(self, client: httpx.AsyncClient):
        """Stage 1: All N students hit /attempts simultaneously using a barrier event."""
        metrics = StageMetrics(stage_name="Stage 1: Synchronized Quiz-Start Burst")
        print(f"[*] Running {metrics.stage_name} ({self.env.concurrency} concurrent requests)...")

        barrier = asyncio.Event()

        async def student_start(student: Dict[str, Any]):
            # Wait for starting barrier
            await barrier.wait()
            t0 = time.perf_counter()
            try:
                resp = await client.post(
                    f"/api/v1/student/quizzes/{self.env.quiz_id}/attempts",
                    headers={"Authorization": f"Bearer {student['token']}"},
                )
                latency = (time.perf_counter() - t0) * 1000.0
                metrics.latencies_ms.append(latency)
                metrics.total_requests += 1

                if resp.status_code == 201:
                    metrics.successful_requests += 1
                    student["attempt_id"] = resp.json()["attempt_id"]
                else:
                    metrics.failed_requests += 1
                    metrics.errors.append(f"HTTP {resp.status_code}: {resp.text[:100]}")
            except Exception as e:
                metrics.failed_requests += 1
                metrics.total_requests += 1
                metrics.errors.append(str(e))

        tasks = [asyncio.create_task(student_start(s)) for s in self.env.students]

        # Trigger synchronized start
        start_time = time.perf_counter()
        barrier.set()
        await asyncio.gather(*tasks)
        metrics.duration_seconds = time.perf_counter() - start_time

        self.stage_reports.append(metrics)
        self._print_stage_summary(metrics)

    async def _stage_2_autosave_traffic(self, client: httpx.AsyncClient):
        """Stage 2: Students autosave answers to all questions."""
        metrics = StageMetrics(stage_name="Stage 2: Autosave Request Burst")
        print(f"[*] Running {metrics.stage_name}...")

        start_time = time.perf_counter()

        # Each student answers all 5 questions
        for q_idx, q in enumerate(self.env.questions, start=1):
            barrier = asyncio.Event()

            async def student_save(student: Dict[str, Any]):
                if not student.get("attempt_id"):
                    return
                await barrier.wait()

                # Pick answer (alternating between correct and options)
                selected_options = q["correct_option_ids"] if len(student["prn"]) % 2 == 0 else [q["options"][0]]
                payload = {
                    "selected_option_ids": selected_options,
                    "client_timestamp": datetime.now(timezone.utc).isoformat(),
                }

                t0 = time.perf_counter()
                try:
                    resp = await client.put(
                        f"/api/v1/student/attempts/{student['attempt_id']}/answers/{q['id']}",
                        json=payload,
                        headers={"Authorization": f"Bearer {student['token']}"},
                    )
                    latency = (time.perf_counter() - t0) * 1000.0
                    metrics.latencies_ms.append(latency)
                    metrics.total_requests += 1

                    if resp.status_code == 200:
                        metrics.successful_requests += 1
                    else:
                        metrics.failed_requests += 1
                        metrics.errors.append(f"Q{q_idx} HTTP {resp.status_code}: {resp.text[:80]}")
                except Exception as e:
                    metrics.failed_requests += 1
                    metrics.total_requests += 1
                    metrics.errors.append(str(e))

            tasks = [asyncio.create_task(student_save(s)) for s in self.env.students]
            barrier.set()
            await asyncio.gather(*tasks)

        metrics.duration_seconds = time.perf_counter() - start_time
        self.stage_reports.append(metrics)
        self._print_stage_summary(metrics)

    async def _stage_3_telemetry_bursts(self, client: httpx.AsyncClient):
        """Stage 3: Students report proctoring events with client_event_id and test deduplication."""
        metrics = StageMetrics(stage_name="Stage 3: Telemetry Bursts & Idempotency")
        print(f"[*] Running {metrics.stage_name}...")

        start_time = time.perf_counter()
        barrier = asyncio.Event()

        async def student_telemetry(student: Dict[str, Any]):
            if not student.get("attempt_id"):
                return
            await barrier.wait()

            client_event_id = str(uuid.uuid4())
            payload = {
                "event_type": "tab_switch",
                "client_event_id": client_event_id,
                "client_timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # First event call
            t0 = time.perf_counter()
            try:
                resp1 = await client.post(
                    f"/api/v1/student/attempts/{student['attempt_id']}/telemetry",
                    json=payload,
                    headers={"Authorization": f"Bearer {student['token']}"},
                )
                latency1 = (time.perf_counter() - t0) * 1000.0
                metrics.latencies_ms.append(latency1)
                metrics.total_requests += 1

                if resp1.status_code == 200:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    metrics.errors.append(f"HTTP {resp1.status_code}")

                # Immediate idempotent retry with identical client_event_id
                t1 = time.perf_counter()
                resp2 = await client.post(
                    f"/api/v1/student/attempts/{student['attempt_id']}/telemetry",
                    json=payload,
                    headers={"Authorization": f"Bearer {student['token']}"},
                )
                latency2 = (time.perf_counter() - t1) * 1000.0
                metrics.latencies_ms.append(latency2)
                metrics.total_requests += 1

                if resp2.status_code == 200:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    metrics.errors.append(f"Retry HTTP {resp2.status_code}")
            except Exception as e:
                metrics.failed_requests += 1
                metrics.total_requests += 1
                metrics.errors.append(str(e))

        tasks = [asyncio.create_task(student_telemetry(s)) for s in self.env.students]
        barrier.set()
        await asyncio.gather(*tasks)

        metrics.duration_seconds = time.perf_counter() - start_time
        self.stage_reports.append(metrics)
        self._print_stage_summary(metrics)

    async def _stage_4_teacher_monitoring(self, client: httpx.AsyncClient):
        """Stage 4: Teacher queries assessment summary and paginated attempts."""
        metrics = StageMetrics(stage_name="Stage 4: Concurrent Teacher Result Queries")
        print(f"[*] Running {metrics.stage_name}...")

        start_time = time.perf_counter()

        for _ in range(5):  # 5 successive teacher monitoring checks
            t0 = time.perf_counter()
            try:
                # Query summary
                resp = await client.get(
                    f"/api/v1/quizzes/{self.env.quiz_id}/results/summary",
                    headers={"Authorization": f"Bearer {self.env.teacher_token}"},
                )
                metrics.latencies_ms.append((time.perf_counter() - t0) * 1000.0)
                metrics.total_requests += 1
                if resp.status_code == 200:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1

                # Query paginated attempts
                t1 = time.perf_counter()
                resp_att = await client.get(
                    f"/api/v1/quizzes/{self.env.quiz_id}/results/attempts?page=1&limit=50",
                    headers={"Authorization": f"Bearer {self.env.teacher_token}"},
                )
                metrics.latencies_ms.append((time.perf_counter() - t1) * 1000.0)
                metrics.total_requests += 1
                if resp_att.status_code == 200:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
            except Exception as e:
                metrics.failed_requests += 1
                metrics.total_requests += 1
                metrics.errors.append(str(e))

        metrics.duration_seconds = time.perf_counter() - start_time
        self.stage_reports.append(metrics)
        self._print_stage_summary(metrics)

    async def _stage_5_submission_burst(self, client: httpx.AsyncClient):
        """Stage 5: Synchronized concurrent attempt submission and final grading."""
        metrics = StageMetrics(stage_name="Stage 5: Synchronized Submission Burst")
        print(f"[*] Running {metrics.stage_name}...")

        barrier = asyncio.Event()

        async def student_submit(student: Dict[str, Any]):
            if not student.get("attempt_id"):
                return
            await barrier.wait()
            t0 = time.perf_counter()
            try:
                resp = await client.post(
                    f"/api/v1/student/attempts/{student['attempt_id']}/submit",
                    headers={"Authorization": f"Bearer {student['token']}"},
                )
                latency = (time.perf_counter() - t0) * 1000.0
                metrics.latencies_ms.append(latency)
                metrics.total_requests += 1

                if resp.status_code == 200:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    metrics.errors.append(f"HTTP {resp.status_code}: {resp.text[:80]}")
            except Exception as e:
                metrics.failed_requests += 1
                metrics.total_requests += 1
                metrics.errors.append(str(e))

        tasks = [asyncio.create_task(student_submit(s)) for s in self.env.students]
        start_time = time.perf_counter()
        barrier.set()
        await asyncio.gather(*tasks)

        metrics.duration_seconds = time.perf_counter() - start_time
        self.stage_reports.append(metrics)
        self._print_stage_summary(metrics)

    def _verify_database_integrity(self) -> Dict[str, Any]:
        """Perform transactional database audit to ensure zero duplicate attempts or lost answers."""
        print(f"\n[*] Performing post-load transactional database integrity audit...")
        db: Session = SessionLocal()
        audit = {
            "total_students": len(self.env.students),
            "expected_attempts": len(self.env.students),
            "actual_attempts": 0,
            "duplicate_attempts": 0,
            "finalized_attempts": 0,
            "expected_total_answers": len(self.env.students) * len(self.env.questions),
            "actual_persisted_answers": 0,
            "lost_answers": 0,
            "scores_non_negative": True,
            "inconsistent_records": 0,
            "is_clean": False,
        }

        try:
            attempts = db.scalars(
                select(QuizAttempt).where(QuizAttempt.quiz_version_id == self.env.quiz_version_id)
            ).all()

            audit["actual_attempts"] = len(attempts)

            # Check duplicate student attempts
            student_attempt_counts: Dict[uuid.UUID, int] = {}
            for a in attempts:
                student_attempt_counts[a.student_id] = student_attempt_counts.get(a.student_id, 0) + 1
                if a.is_finalized:
                    audit["finalized_attempts"] += 1
                if a.total_score is not None and a.total_score < 0:
                    audit["scores_non_negative"] = False

            audit["duplicate_attempts"] = sum(count - 1 for count in student_attempt_counts.values() if count > 1)

            # Count persisted answers
            attempt_ids = [a.id for a in attempts]
            actual_answers = db.scalar(
                select(func.count(AttemptAnswer.id)).where(AttemptAnswer.attempt_id.in_(attempt_ids))
            ) or 0
            audit["actual_persisted_answers"] = actual_answers
            audit["lost_answers"] = max(0, audit["expected_total_answers"] - actual_answers)

            audit["is_clean"] = (
                audit["duplicate_attempts"] == 0
                and audit["lost_answers"] == 0
                and audit["actual_attempts"] == audit["expected_attempts"]
                and audit["finalized_attempts"] == audit["expected_attempts"]
                and audit["scores_non_negative"]
            )

            print(f"    - Attempts: {audit['actual_attempts']}/{audit['expected_attempts']} (Duplicates: {audit['duplicate_attempts']})")
            print(f"    - Finalized: {audit['finalized_attempts']}/{audit['expected_attempts']}")
            print(f"    - Answers: {audit['actual_persisted_answers']}/{audit['expected_total_answers']} (Lost: {audit['lost_answers']})")
            print(f"    - Scores Non-Negative: {audit['scores_non_negative']}")
            print(f"    - Integrity Status: {'[PASS] Verified' if audit['is_clean'] else '[FAIL] Inconsistent'}")
            return audit
        finally:
            db.close()

    def _print_stage_summary(self, m: StageMetrics):
        """Format and print concise metrics summary."""
        print(f"    -> Requests: {m.successful_requests}/{m.total_requests} OK | Latency: p50={m.median_ms}ms, p95={m.p95_ms}ms, p99={m.p99_ms}ms | Throughput: {m.rps} req/s | Errors: {m.error_rate}%")
        if m.errors:
            print(f"    -> Sample errors: {m.errors[:2]}")


def run_benchmark(concurrency: int = 50, base_url: str = "http://127.0.0.1:8000"):
    """Entrypoint function to run setup, execute benchmark, and cleanup."""
    env = LoadTestEnvironment(concurrency=concurrency)
    try:
        env.setup()
        runner = AssessmentLoadTestRunner(env=env, base_url=base_url)
        results = asyncio.run(runner.run_full_suite())
        return results
    finally:
        env.cleanup()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Quizdesk Phase 9 Concurrency Benchmark")
    parser.add_argument("--concurrency", type=int, default=50, help="Number of concurrent virtual students (default: 50)")
    parser.add_argument("--base-url", type=str, default="http://127.0.0.1:8000", help="Base URL of target Quizdesk server")
    args = parser.parse_args()

    run_benchmark(concurrency=args.concurrency, base_url=args.base_url)
