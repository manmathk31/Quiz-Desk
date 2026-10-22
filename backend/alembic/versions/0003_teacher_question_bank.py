"""Support teacher reusable question bank and creator association (DEC-006)

Revision ID: 0003_question_bank
Revises: 0002_integrity
Create Date: 2026-10-23 02:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_question_bank'
down_revision: Union[str, None] = '0002_integrity'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Allow questions to exist in teacher question bank without being attached to a quiz version yet
    op.alter_column(
        'questions',
        'quiz_version_id',
        existing_type=sa.UUID(),
        nullable=True,
    )

    # 2. Add created_by_id column referencing users.id for teacher ownership
    op.add_column(
        'questions',
        sa.Column('created_by_id', sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        'fk_questions_created_by_id_users',
        'questions',
        'users',
        ['created_by_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    op.create_index(
        'ix_questions_created_by_id',
        'questions',
        ['created_by_id'],
    )

    # 3. Enforce that every question belongs to either a quiz version or a teacher question bank (or both)
    op.create_check_constraint(
        'ck_question_bank_or_version',
        'questions',
        '(quiz_version_id IS NOT NULL) OR (created_by_id IS NOT NULL)',
    )


def downgrade() -> None:
    # 3. Drop check constraint
    op.drop_constraint('ck_question_bank_or_version', 'questions', type_='check')

    # 2. Drop created_by_id index, foreign key, and column
    op.drop_index('ix_questions_created_by_id', table_name='questions')
    op.drop_constraint('fk_questions_created_by_id_users', 'questions', type_='foreignkey')
    op.drop_column('questions', 'created_by_id')

    # 1. Revert quiz_version_id to nullable=False
    op.alter_column(
        'questions',
        'quiz_version_id',
        existing_type=sa.UUID(),
        nullable=False,
    )
