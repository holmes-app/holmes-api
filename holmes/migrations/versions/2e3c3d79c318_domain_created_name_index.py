"""Domain: Created name index

Revision ID: 2e3c3d79c318
Revises: 5592365e4624
Create Date: 2014-12-03 14:39:47.626645

"""

# revision identifiers, used by Alembic.
revision = '2e3c3d79c318'
down_revision = '5592365e4624'

from alembic import op


def upgrade():
    op.execute('CREATE INDEX idx_name on domains (name(220))')


def downgrade():
    op.drop_index('idx_name', 'domains')
