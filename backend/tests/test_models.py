"""Automated unit test suite verifying SQLAlchemy models and Alembic migration metadata."""
import os
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.models import (
    Base,
    UserRole,
    QuizStatus,
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

    # QuizVersion immutability constraint: unique (quiz_id, version_number)
    qv_constraints = [
        c.name for c in tables["quiz_versions"].constraints if c.name == "uq_quiz_version_number"
    ]
    assert "uq_quiz_version_number" in qv_constraints

    # QuizAssignment uniqueness: unique (quiz_id, student_prn)
    qa_constraints = [
        c.name for c in tables["quiz_assignments"].constraints if c.name == "uq_quiz_assignment_prn"
    ]
    assert "uq_quiz_assignment_prn" in qa_constraints

    # QuizAttempt uniqueness: unique (quiz_version_id, student_id, attempt_number)
    attempt_constraints = [
        c.name
        for c in tables["quiz_attempts"].constraints
        if c.name == "uq_attempt_number_per_student"
    ]
    assert "uq_attempt_number_per_student" in attempt_constraints


def test_enum_specifications():
    """Verify domain enums match confirmed project decisions."""
    assert set(UserRole) == {"student", "teacher", "admin"}
    assert set(QuizStatus) == {"draft", "published", "closed", "archived"}
    assert set(QuestionType) == {"single_choice", "multiple_choice", "true_false"}
    assert set(AttemptStatus) == {"in_progress", "submitted", "expired", "cancelled"}
    assert set(GradingStatus) == {"withheld", "released", "manually_adjusted"}


def test_alembic_migration_chain():
    """Verify Alembic discovery and validity of initial revision."""
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    alembic_ini_path = os.path.join(backend_dir, "alembic.ini")

    config = Config(alembic_ini_path)
    script = ScriptDirectory.from_config(config)

    heads = script.get_heads()
    assert len(heads) == 1
    assert heads[0] == "0001_initial_schema"

    revision = script.get_revision("0001_initial_schema")
    assert revision is not None
    assert revision.down_revision is None
