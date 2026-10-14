"""add_attrition_payroll_and_salary_revisions

Revision ID: f192a8e41bc3
Revises: 3e19e4f8a7d2
Create Date: 2026-10-14 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f192a8e41bc3'
down_revision: Union[str, Sequence[str], None] = '3e19e4f8a7d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('employees', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('employees', sa.Column('work_mode', sa.String(length=50), nullable=True))
    op.add_column('employees', sa.Column('employment_status', sa.String(length=50), nullable=True))
    op.add_column('employees', sa.Column('exit_type', sa.String(length=50), nullable=True))
    op.add_column('employees', sa.Column('exit_reason', sa.String(length=255), nullable=True))
    op.add_column('employees', sa.Column('pf_applicable', sa.Boolean(), nullable=True))
    op.add_column('employees', sa.Column('esi_applicable', sa.Boolean(), nullable=True))

    op.create_table(
        'salary_revisions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('revision_code', sa.String(length=20), nullable=True),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('revision_reason', sa.String(length=100), nullable=True),
        sa.Column('previous_annual_fixed', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('new_annual_fixed', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('pct_change', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('role_id_after', sa.String(length=20), nullable=True),
        sa.Column('approved_by', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_salary_revisions_revision_code'), 'salary_revisions', ['revision_code'], unique=True)
    op.create_index(op.f('ix_salary_revisions_employee_id'), 'salary_revisions', ['employee_id'], unique=False)
    op.create_index(op.f('ix_salary_revisions_effective_from'), 'salary_revisions', ['effective_from'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_salary_revisions_effective_from'), table_name='salary_revisions')
    op.drop_index(op.f('ix_salary_revisions_employee_id'), table_name='salary_revisions')
    op.drop_index(op.f('ix_salary_revisions_revision_code'), table_name='salary_revisions')
    op.drop_table('salary_revisions')

    op.drop_column('employees', 'esi_applicable')
    op.drop_column('employees', 'pf_applicable')
    op.drop_column('employees', 'exit_reason')
    op.drop_column('employees', 'exit_type')
    op.drop_column('employees', 'employment_status')
    op.drop_column('employees', 'work_mode')
    op.drop_column('employees', 'date_of_birth')
