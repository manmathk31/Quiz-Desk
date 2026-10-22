"""Initial schema creation for Quizdesk

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-23 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='student'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])

    # 2. Student Profiles Table
    op.create_table(
        'student_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prn', sa.String(length=64), nullable=False),
        sa.Column('current_division', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', name='uq_student_profiles_user_id'),
    )
    op.create_index('ix_student_profiles_prn', 'student_profiles', ['prn'], unique=True)

    # 3. Quizzes Table
    op.create_table(
        'quizzes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('course_code', sa.String(length=64), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('current_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_quizzes_course_code', 'quizzes', ['course_code'])
    op.create_index('ix_quizzes_created_by_id', 'quizzes', ['created_by_id'])
    op.create_index('ix_quizzes_status', 'quizzes', ['status'])

    # 4. Quiz Versions Table
    op.create_table(
        'quiz_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('opens_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('closes_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('allow_backtracking', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('shuffle_questions', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('shuffle_options', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('tab_switch_limit', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('tab_switch_penalty_marks', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('is_results_released', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('results_released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('results_released_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('quiz_id', 'version_number', name='uq_quiz_version_number'),
    )
    op.create_index('ix_quiz_versions_quiz_id', 'quiz_versions', ['quiz_id'])

    # 5. Questions Table
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quiz_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quiz_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_type', sa.String(length=32), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('positive_marks', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.00'),
        sa.Column('negative_marks', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_questions_quiz_version_id', 'questions', ['quiz_version_id'])

    # 6. Question Options Table
    op.create_table(
        'question_options',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_question_options_question_id', 'question_options', ['question_id'])

    # 7. Quiz Assignments Table
    op.create_table(
        'quiz_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_prn', sa.String(length=64), nullable=False),
        sa.Column('student_email', sa.String(length=255), nullable=False),
        sa.Column('student_name', sa.String(length=255), nullable=False),
        sa.Column('division', sa.String(length=32), nullable=False),
        sa.Column('assigned_student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('quiz_id', 'student_prn', name='uq_quiz_assignment_prn'),
    )
    op.create_index('ix_quiz_assignments_quiz_id', 'quiz_assignments', ['quiz_id'])
    op.create_index('ix_quiz_assignments_student_prn', 'quiz_assignments', ['student_prn'])
    op.create_index('ix_quiz_assignments_lookup', 'quiz_assignments', ['quiz_id', 'student_email'])

    # 8. Quiz Attempts Table
    op.create_table(
        'quiz_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quiz_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quiz_versions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='in_progress'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deadline_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_score', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('grading_status', sa.String(length=32), nullable=False, server_default='withheld'),
        sa.Column('is_finalized', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('tab_switch_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('quiz_version_id', 'student_id', 'attempt_number', name='uq_attempt_number_per_student'),
    )
    op.create_index('ix_quiz_attempts_quiz_version_id', 'quiz_attempts', ['quiz_version_id'])
    op.create_index('ix_quiz_attempts_student_id', 'quiz_attempts', ['student_id'])
    op.create_index('ix_quiz_attempts_status', 'quiz_attempts', ['status'])

    # 9. Attempt Answers Table
    op.create_table(
        'attempt_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quiz_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('questions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('selected_option_ids', sa.JSON(), nullable=False),
        sa.Column('is_marked_for_review', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('awarded_marks', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('saved_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('attempt_id', 'question_id', name='uq_attempt_question_answer'),
    )
    op.create_index('ix_attempt_answers_attempt_id', 'attempt_answers', ['attempt_id'])
    op.create_index('ix_attempt_answers_question_id', 'attempt_answers', ['question_id'])

    # 10. Attempt Telemetry Events Table
    op.create_table(
        'attempt_telemetry_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quiz_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('event_data', sa.JSON(), nullable=True),
    )
    op.create_index('ix_attempt_telemetry_events_attempt_id', 'attempt_telemetry_events', ['attempt_id'])

    # 11. Grade Adjustments Table
    op.create_table(
        'grade_adjustments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quiz_attempts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('adjusted_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('previous_score', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('new_score', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_grade_adjustments_attempt_id', 'grade_adjustments', ['attempt_id'])
    op.create_index('ix_grade_adjustments_adjusted_by_id', 'grade_adjustments', ['adjusted_by_id'])

    # 12. Audit Events Table
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', sa.String(length=64), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_audit_events_action', 'audit_events', ['action'])
    op.create_index('ix_audit_events_created_at', 'audit_events', ['created_at'])

    # 13. Import Jobs Table
    op.create_table(
        'import_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('import_type', sa.String(length=64), nullable=False),
        sa.Column('target_quiz_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quizzes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valid_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_import_jobs_created_by_id', 'import_jobs', ['created_by_id'])
    op.create_index('ix_import_jobs_target_quiz_id', 'import_jobs', ['target_quiz_id'])


def downgrade() -> None:
    # Drop in reverse order of foreign key dependencies
    op.drop_table('import_jobs')
    op.drop_table('audit_events')
    op.drop_table('grade_adjustments')
    op.drop_table('attempt_telemetry_events')
    op.drop_table('attempt_answers')
    op.drop_table('quiz_attempts')
    op.drop_table('quiz_assignments')
    op.drop_table('question_options')
    op.drop_table('questions')
    op.drop_table('quiz_versions')
    op.drop_table('quizzes')
    op.drop_table('student_profiles')
    op.drop_table('users')
