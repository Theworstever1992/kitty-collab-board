"""initial schema from create_tables() baseline

Revision ID: 0001
Revises: 
Create Date: 2026-03-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All tables were originally created by Base.metadata.create_all() in create_tables().
    # This migration captures that baseline for future incremental migrations.
    # Running `alembic upgrade head` on a fresh DB will create all tables;
    # existing deployments that used create_tables() should stamp with:
    #   alembic stamp 0001
    pass


def downgrade() -> None:
    pass
