"""Change fact to contain less info

Revision ID: 256faac818c5
Revises: 39091f5a3e5f
Create Date: 2013-12-02 21:29:59.676698

"""

# revision identifiers, used by Alembic.
revision = '256faac818c5'
down_revision = '39091f5a3e5f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('facts', 'title')
    op.drop_column('facts', 'unit')


def downgrade():
    op.add_column('facts', sa.Column('title', sa.String(2000), nullable=False))
    op.add_column('facts', sa.Column('unit', sa.String(2000), nullable=False))
