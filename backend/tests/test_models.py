"""Automated unit test suite verifying SQLAlchemy models and Alembic migration metadata."""
import os
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.models import (
    Base,
    UserRole,
    QuizStatus,
    MultiAnswerPolicy,
    QuestionType,
    AttemptStatus,
    GradingStatus,
)


def test_sqlalchemy_metadata_table_registration():
    """Verify all 13 core domain tables are registered in Base.metadata."""
    expected_tables = {
        "users",
        "student_profiles",
        "quizzes",
        "quiz_versions",
        "questions",
        "question_options",
        "quiz_assignments",
        "quiz_attempts",
        "attempt_answers",
        "attempt_telemetry_events",
        "grade_adjustments",
        "audit_events",
        "import_jobs",
    }
    registered_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(registered_tables), (
        f"Missing tables: {expected_tables - registered_tables}"
    )


def test_unique_constraints_and_foreign_keys():
    """Verify critical integrity constraints across tables."""
    tables = Base.metadata.tables

    # User & StudentProfile
    assert "email" in tables["users"].columns
    assert tables["users"].columns["email"].unique or any(
        idx.unique for idx in tables["users"].indexes if "email" in idx.columns
    )
    assert "prn" in tables["student_profiles"].columns

    # QuizVersion immutability & protection: unique (quiz_id, version_number) & ON DELETE RESTRICT
    qv_constraints = {c.name for c in tables["quiz_versions"].constraints}
    assert "uq_quiz_version_number" in qv_constraints
    assert "ck_quiz_version_duration" in qv_constraints
    assert "ck_quiz_version_max_attempts" in qv_constraints
    assert "ck_quiz_version_time_window" in qv_constraints
    assert "ck_quiz_version_tab_limit" in qv_constraints
    assert "ck_quiz_version_tab_penalty" in qv_constraints

    quiz_fks = [fk for fk in tables["quiz_versions"].foreign_keys if fk.column.table.name == "quizzes"]
    assert len(quiz_fks) == 1
    assert quiz_fks[0].ondelete == "RESTRICT"

    # QuizAssignment uniqueness: unique (quiz_id, student_prn) AND (quiz_id, student_email)
    qa_constraints = {c.name for c in tables["quiz_assignments"].constraints}
    assert "uq_quiz_assignment_prn" in qa_constraints
    assert "uq_quiz_assignment_email" in qa_constraints

    # Question constraints
    q_constraints = {c.name for c in tables["questions"].constraints}
    assert "ck_question_positive_marks" in q_constraints
    assert "ck_question_negative_marks" in q_constraints

    # QuizAttempt constraints
    attempt_constraints = {c.name for c in tables["quiz_attempts"].constraints}
    assert "uq_attempt_number_per_student" in attempt_constraints
    assert "ck_quiz_attempt_number" in attempt_constraints
    assert "ck_quiz_attempt_deadline" in attempt_constraints
    assert "ck_quiz_attempt_tab_count" in attempt_constraints


def test_enum_specifications():
    """Verify domain enums match confirmed project decisions."""
    assert set(UserRole) == {"student", "teacher", "admin"}
    assert set(QuizStatus) == {"draft", "published", "closed", "archived"}
    assert set(MultiAnswerPolicy) == {"all_or_nothing", "partial_with_penalty", "partial_no_penalty"}
    assert set(QuestionType) == {"single_choice", "multiple_choice", "true_false"}
    assert set(AttemptStatus) == {"in_progress", "submitted", "expired", "cancelled"}
    assert set(GradingStatus) == {"pending", "auto_graded", "manually_adjusted"}


def test_alembic_migration_chain():
    """Verify Alembic discovery and sequential migration chain."""
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    alembic_ini_path = os.path.join(backend_dir, "alembic.ini")

    config = Config(alembic_ini_path)
    script = ScriptDirectory.from_config(config)

    heads = script.get_heads()
    assert len(heads) == 1
    assert heads[0] == "0002_integrity"

    rev2 = script.get_revision("0002_integrity")
    assert rev2 is not None
    assert rev2.down_revision == "0001_initial_schema"

    rev1 = script.get_revision("0001_initial_schema")
    assert rev1 is not None
    assert rev1.down_revision is None
