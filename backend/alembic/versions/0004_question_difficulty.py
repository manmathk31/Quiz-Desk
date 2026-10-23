"""Add question difficulty level and constraint (Milestone 4B)

Revision ID: 0004_question_difficulty
Revises: 0003_question_bank
Create Date: 2026-10-23 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_question_difficulty'
down_revision: Union[str, None] = '0003_question_bank'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add difficulty column with documented safe default 'medium' for existing rows
    op.add_column(
        'questions',
        sa.Column(
            'difficulty',
            sa.String(length=16),
            nullable=False,
            server_default='medium',
        ),
    )

    # 2. Create index on difficulty for performant filtering
    op.create_index(
        'ix_questions_difficulty',
        'questions',
        ['difficulty'],
    )

    # 3. Add check constraint enforcing valid difficulty values
    op.create_check_constraint(
        'ck_question_difficulty_enum',
        'questions',
        "difficulty IN ('easy', 'medium', 'hard')",
    )


def downgrade() -> None:
    # 3. Drop check constraint
    op.drop_constraint('ck_question_difficulty_enum', 'questions', type_='check')

    # 2. Drop index
    op.drop_index('ix_questions_difficulty', table_name='questions')

    # 1. Drop column
    op.drop_column('questions', 'difficulty')
