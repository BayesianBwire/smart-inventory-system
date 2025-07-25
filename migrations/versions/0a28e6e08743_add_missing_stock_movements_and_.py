"""Add missing stock_movements and dashboards tables

Revision ID: 0a28e6e08743
Revises: 032bdca9623b
Create Date: 2025-07-23 02:36:04.907952

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a28e6e08743'
down_revision = '032bdca9623b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    
    # Create stock_movements table
    op.create_table('stock_movements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('movement_type', sa.String(length=50), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('previous_quantity', sa.Integer(), nullable=False),
    sa.Column('new_quantity', sa.Integer(), nullable=False),
    sa.Column('unit_cost', sa.Float(), nullable=True),
    sa.Column('total_cost', sa.Float(), nullable=True),
    sa.Column('reference', sa.String(length=100), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_by', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create dashboards table
    op.create_table('dashboards',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('dashboard_type', sa.String(length=50), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=True),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('layout_config', sa.JSON(), nullable=True),
    sa.Column('filters', sa.JSON(), nullable=True),
    sa.Column('refresh_interval', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create dashboard_widgets table
    op.create_table('dashboard_widgets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dashboard_id', sa.Integer(), nullable=True),
    sa.Column('widget_type', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('position_x', sa.Integer(), nullable=True),
    sa.Column('position_y', sa.Integer(), nullable=True),
    sa.Column('width', sa.Integer(), nullable=True),
    sa.Column('height', sa.Integer(), nullable=True),
    sa.Column('data_source', sa.String(length=100), nullable=True),
    sa.Column('chart_config', sa.JSON(), nullable=True),
    sa.Column('filters', sa.JSON(), nullable=True),
    sa.Column('is_visible', sa.Boolean(), nullable=True),
    sa.Column('refresh_rate', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['dashboard_id'], ['dashboards.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('dashboard_widgets')
    op.drop_table('dashboards')
    op.drop_table('stock_movements')
    # ### end Alembic commands ###
