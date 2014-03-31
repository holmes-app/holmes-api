"""idx requests by status, completed

Revision ID: 7f4a3b8c55d
Revises: 4b96dd9974bb
Create Date: 2014-03-31 17:39:40.858182

"""

# revision identifiers, used by Alembic.
revision = '7f4a3b8c55d'
down_revision = '4b96dd9974bb'

from alembic import op


def upgrade():
    op.create_index('idx_status_complete', 'requests', ['status_code', 'completed_date'])


def downgrade():
    op.drop_index('idx_status_complete', 'requests')
