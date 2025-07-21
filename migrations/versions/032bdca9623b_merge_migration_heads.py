y"""Merge migration heads

Revision ID: 032bdca9623b
Revises: 0bf4fef7d124, fabcb2dba27f
Create Date: 2025-07-10 18:35:32.641119

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '032bdca9623b'
down_revision = ('0bf4fef7d124', 'fabcb2dba27f')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
