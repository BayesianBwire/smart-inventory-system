"""Update leave_requests table with status field

Revision ID: 4fcda1202302
Revises: 276582252df1
Create Date: 2025-07-02 01:20:48.771989

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4fcda1202302'
down_revision = '276582252df1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('leave_requests', schema=None) as batch_op:
        batch_op.alter_column('end_date',
               existing_type=sa.DATE(),
               nullable=False)
        batch_op.alter_column('reason',
               existing_type=sa.VARCHAR(length=250),
               type_=sa.String(length=255),
               existing_nullable=True)
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('leave_requests', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
        batch_op.alter_column('reason',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=250),
               existing_nullable=True)
        batch_op.alter_column('end_date',
               existing_type=sa.DATE(),
               nullable=True)

    # ### end Alembic commands ###
