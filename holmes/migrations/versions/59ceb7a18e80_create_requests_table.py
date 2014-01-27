"""create requests table

Revision ID: 59ceb7a18e80
Revises: 49c5cb27e7f6
Create Date: 2014-01-24 18:48:22.491856

"""

# revision identifiers, used by Alembic.
revision = '59ceb7a18e80'
down_revision = '49c5cb27e7f6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'requests',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('domain_name', sa.String(120), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('effective_url', sa.Text(), nullable=False),
        sa.Column('status_code', sa.Integer, nullable=False),
        sa.Column('response_time', sa.Float, nullable=False)
    )


def downgrade():
    op.drop_table('requests')
