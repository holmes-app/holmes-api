"""Requests: Create indexes

Revision ID: 22bc83869dbe
Revises: 556bb65b2a84
Create Date: 2014-01-27 14:02:34.377544

"""

# revision identifiers, used by Alembic.
revision = '22bc83869dbe'
down_revision = '556bb65b2a84'

from alembic import op


def upgrade():
    op.create_index(
        'idx_request',
        'requests',
        ['completed_date', 'domain_name', 'status_code'])


def downgrade():
    op.drop_index('idx_request', 'requests'),
