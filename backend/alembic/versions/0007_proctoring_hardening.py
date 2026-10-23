"""Harden assessment proctoring, configurable penalty rules, and telemetry idempotency (Phase 8A, DEC-021)

Revision ID: 0007_proctoring_hardening
Revises: 0006_attempt_shuffling
Create Date: 2026-10-23 12:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_proctoring_hardening'
down_revision: Union[str, None] = '0006_attempt_shuffling'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add proctoring policy fields to quiz_versions
    op.add_column(
        'quiz_versions',
        sa.Column('max_proctoring_deduction', sa.Numeric(precision=5, scale=2), server_default='5.00', nullable=False),
    )
    op.add_column(
        'quiz_versions',
        sa.Column('enable_copy_paste_restriction', sa.Boolean(), server_default='true', nullable=False),
    )
    op.add_column(
        'quiz_versions',
        sa.Column('count_copy_paste_violations', sa.Boolean(), server_default='true', nullable=False),
    )
    op.add_column(
        'quiz_versions',
        sa.Column('require_fullscreen', sa.Boolean(), server_default='true', nullable=False),
    )
    op.add_column(
        'quiz_versions',
        sa.Column('count_fullscreen_exit_violations', sa.Boolean(), server_default='true', nullable=False),
    )
    op.add_column(
        'quiz_versions',
        sa.Column('count_tab_switch_violations', sa.Boolean(), server_default='true', nullable=False),
    )
    op.add_column(
        'quiz_versions',
        sa.Column('count_dev_tools_violations', sa.Boolean(), server_default='true', nullable=False),
    )
    op.add_column(
        'quiz_versions',
        sa.Column('enable_proctoring_warnings', sa.Boolean(), server_default='true', nullable=False),
    )
    op.create_check_constraint(
        'ck_quiz_version_max_deduction',
        'quiz_versions',
        'max_proctoring_deduction >= 0',
    )

    # 2. Add proctoring deduction and violation_count to quiz_attempts
    op.add_column(
        'quiz_attempts',
        sa.Column('proctoring_deduction', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
    )
    op.add_column(
        'quiz_attempts',
        sa.Column('violation_count', sa.Integer(), server_default='0', nullable=False),
    )
    op.create_check_constraint(
        'ck_quiz_attempt_deduction',
        'quiz_attempts',
        'proctoring_deduction >= 0',
    )
    op.create_check_constraint(
        'ck_quiz_attempt_violation_count',
        'quiz_attempts',
        'violation_count >= 0',
    )

    # 3. Add client_event_id and index to attempt_telemetry_events for idempotency
    op.add_column(
        'attempt_telemetry_events',
        sa.Column('client_event_id', sa.String(length=64), nullable=True),
    )
    op.create_index(
        'ix_attempt_telemetry_events_client_event_id',
        'attempt_telemetry_events',
        ['client_event_id'],
        unique=False,
    )


def downgrade() -> None:
    # 3. Drop client_event_id index and column from attempt_telemetry_events
    op.drop_index('ix_attempt_telemetry_events_client_event_id', table_name='attempt_telemetry_events')
    op.drop_column('attempt_telemetry_events', 'client_event_id')

    # 2. Drop constraints and columns from quiz_attempts
    op.drop_constraint('ck_quiz_attempt_violation_count', 'quiz_attempts', type_='check')
    op.drop_constraint('ck_quiz_attempt_deduction', 'quiz_attempts', type_='check')
    op.drop_column('quiz_attempts', 'violation_count')
    op.drop_column('quiz_attempts', 'proctoring_deduction')

    # 1. Drop constraint and columns from quiz_versions
    op.drop_constraint('ck_quiz_version_max_deduction', 'quiz_versions', type_='check')
    op.drop_column('quiz_versions', 'enable_proctoring_warnings')
    op.drop_column('quiz_versions', 'count_dev_tools_violations')
    op.drop_column('quiz_versions', 'count_tab_switch_violations')
    op.drop_column('quiz_versions', 'count_fullscreen_exit_violations')
    op.drop_column('quiz_versions', 'require_fullscreen')
    op.drop_column('quiz_versions', 'count_copy_paste_violations')
    op.drop_column('quiz_versions', 'enable_copy_paste_restriction')
    op.drop_column('quiz_versions', 'max_proctoring_deduction')
