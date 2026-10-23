"""Add attempt shuffling order, client timestamp for out-of-order save protection, and student status index (Phase 6)

Revision ID: 0006_attempt_shuffling
Revises: 0005_assignment_lifecycle
Create Date: 2026-10-23 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006_attempt_shuffling'
down_revision: Union[str, None] = '0005_assignment_lifecycle'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add question_order JSON column to quiz_attempts
    op.add_column(
        'quiz_attempts',
        sa.Column(
            'question_order',
            sa.JSON(),
            nullable=True,
        ),
    )

    # 2. Add option_order JSON column to quiz_attempts
    op.add_column(
        'quiz_attempts',
        sa.Column(
            'option_order',
            sa.JSON(),
            nullable=True,
        ),
    )

    # 3. Add client_timestamp column to attempt_answers
    op.add_column(
        'attempt_answers',
        sa.Column(
            'client_timestamp',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # 4. Create composite index on student_id and status for fast in-progress attempt lookup
    op.create_index(
        'ix_quiz_attempts_student_status',
        'quiz_attempts',
        ['student_id', 'status'],
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_quiz_attempts_student_status', table_name='quiz_attempts')

    # Drop columns
    op.drop_column('attempt_answers', 'client_timestamp')
    op.drop_column('quiz_attempts', 'option_order')
    op.drop_column('quiz_attempts', 'question_order')
