"""Add assignment active status, revocation metadata, and active index (Phase 5)

Revision ID: 0005_assignment_lifecycle
Revises: 0004_question_difficulty
Create Date: 2026-10-23 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0005_assignment_lifecycle'
down_revision: Union[str, None] = '0004_question_difficulty'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_active column defaulting to true
    op.add_column(
        'quiz_assignments',
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
    )

    # 2. Add revoked_at timestamp column
    op.add_column(
        'quiz_assignments',
        sa.Column(
            'revoked_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # 3. Add revoked_by_id foreign key column
    op.add_column(
        'quiz_assignments',
        sa.Column(
            'revoked_by_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )

    # 4. Create active status index
    op.create_index(
        'ix_quiz_assignments_active',
        'quiz_assignments',
        ['quiz_id', 'is_active'],
    )
    op.create_index(
        'ix_quiz_assignments_revoked_by_id',
        'quiz_assignments',
        ['revoked_by_id'],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_quiz_assignments_revoked_by_id', table_name='quiz_assignments')
    op.drop_index('ix_quiz_assignments_active', table_name='quiz_assignments')

    # Drop columns
    op.drop_column('quiz_assignments', 'revoked_by_id')
    op.drop_column('quiz_assignments', 'revoked_at')
    op.drop_column('quiz_assignments', 'is_active')
