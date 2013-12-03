"""Change violation to contain less info

Revision ID: 21087e990aa8
Revises: 256faac818c5
Create Date: 2013-12-02 22:11:34.036524

"""

# revision identifiers, used by Alembic.
revision = '21087e990aa8'
down_revision = '256faac818c5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('violations', 'title')
    op.drop_column('violations', 'description')
    op.add_column('violations', sa.Column('value', sa.Text, nullable=True))


def downgrade():
    op.add_column('violations', sa.Column('title', sa.String(2000), nullable=False))
    op.add_column('violations', sa.Column('description', sa.Text, nullable=False))
    op.drop_column('violations', 'value')
