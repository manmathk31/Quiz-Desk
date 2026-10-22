"""Strengthen assessment data integrity constraints

Revision ID: 0002_integrity
Revises: 0001_initial_schema
Create Date: 2026-10-23 01:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_integrity'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update quiz_assignments: add unique constraint on (quiz_id, student_email)
    op.create_unique_constraint(
        'uq_quiz_assignment_email',
        'quiz_assignments',
        ['quiz_id', 'student_email'],
    )

    # 2. Update quiz_versions:
    # 2a. Add is_published column and index
    op.add_column(
        'quiz_versions',
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_index('ix_quiz_versions_is_published', 'quiz_versions', ['is_published'])

    # 2b. Add multi_answer_policy column
    op.add_column(
        'quiz_versions',
        sa.Column('multi_answer_policy', sa.String(length=32), nullable=False, server_default='all_or_nothing'),
    )

    # 2c. Change quiz_id foreign key from CASCADE to RESTRICT to protect published versions
    op.drop_constraint('quiz_versions_quiz_id_fkey', 'quiz_versions', type_='foreignkey')
    op.create_foreign_key(
        'fk_quiz_versions_quiz_id_quizzes',
        'quiz_versions',
        'quizzes',
        ['quiz_id'],
        ['id'],
        ondelete='RESTRICT',
    )

    # 2d. Add check constraints on quiz_versions
    op.create_check_constraint(
        'ck_quiz_version_duration',
        'quiz_versions',
        'duration_minutes > 0',
    )
    op.create_check_constraint(
        'ck_quiz_version_max_attempts',
        'quiz_versions',
        'max_attempts > 0',
    )
    op.create_check_constraint(
        'ck_quiz_version_time_window',
        'quiz_versions',
        'closes_at > opens_at',
    )
    op.create_check_constraint(
        'ck_quiz_version_tab_limit',
        'quiz_versions',
        'tab_switch_limit >= 0',
    )
    op.create_check_constraint(
        'ck_quiz_version_tab_penalty',
        'quiz_versions',
        'tab_switch_penalty_marks >= 0',
    )

    # 3. Update questions: add check constraints on scoring fields
    op.create_check_constraint(
        'ck_question_positive_marks',
        'questions',
        'positive_marks > 0',
    )
    op.create_check_constraint(
        'ck_question_negative_marks',
        'questions',
        'negative_marks >= 0',
    )

    # 4. Update quiz_attempts:
    # 4a. Update default for grading_status from withheld to pending
    op.alter_column(
        'quiz_attempts',
        'grading_status',
        server_default='pending',
    )
    # Migrate any rows that might exist with legacy 'withheld' status to 'pending'
    op.execute("UPDATE quiz_attempts SET grading_status = 'pending' WHERE grading_status = 'withheld'")

    # 4b. Add check constraints on quiz_attempts
    op.create_check_constraint(
        'ck_quiz_attempt_number',
        'quiz_attempts',
        'attempt_number >= 1',
    )
    op.create_check_constraint(
        'ck_quiz_attempt_deadline',
        'quiz_attempts',
        'deadline_at >= started_at',
    )
    op.create_check_constraint(
        'ck_quiz_attempt_tab_count',
        'quiz_attempts',
        'tab_switch_count >= 0',
    )


def downgrade() -> None:
    # 4. Revert quiz_attempts
    op.drop_constraint('ck_quiz_attempt_tab_count', 'quiz_attempts', type_='check')
    op.drop_constraint('ck_quiz_attempt_deadline', 'quiz_attempts', type_='check')
    op.drop_constraint('ck_quiz_attempt_number', 'quiz_attempts', type_='check')
    op.execute("UPDATE quiz_attempts SET grading_status = 'withheld' WHERE grading_status = 'pending'")
    op.alter_column(
        'quiz_attempts',
        'grading_status',
        server_default='withheld',
    )

    # 3. Revert questions
    op.drop_constraint('ck_question_negative_marks', 'questions', type_='check')
    op.drop_constraint('ck_question_positive_marks', 'questions', type_='check')

    # 2. Revert quiz_versions
    op.drop_constraint('ck_quiz_version_tab_penalty', 'quiz_versions', type_='check')
    op.drop_constraint('ck_quiz_version_tab_limit', 'quiz_versions', type_='check')
    op.drop_constraint('ck_quiz_version_time_window', 'quiz_versions', type_='check')
    op.drop_constraint('ck_quiz_version_max_attempts', 'quiz_versions', type_='check')
    op.drop_constraint('ck_quiz_version_duration', 'quiz_versions', type_='check')

    op.drop_constraint('fk_quiz_versions_quiz_id_quizzes', 'quiz_versions', type_='foreignkey')
    op.create_foreign_key(
        'quiz_versions_quiz_id_fkey',
        'quiz_versions',
        'quizzes',
        ['quiz_id'],
        ['id'],
        ondelete='CASCADE',
    )

    op.drop_column('quiz_versions', 'multi_answer_policy')
    op.drop_index('ix_quiz_versions_is_published', 'quiz_versions')
    op.drop_column('quiz_versions', 'is_published')

    # 1. Revert quiz_assignments
    op.drop_constraint('uq_quiz_assignment_email', 'quiz_assignments', type_='unique')
