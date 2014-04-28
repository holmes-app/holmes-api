"""Requests: Adding index for completed_date

Revision ID: 2db70040b01b
Revises: 519b66176c0c
Create Date: 2014-04-28 15:58:12.331243

"""

# revision identifiers, used by Alembic.
revision = '2db70040b01b'
down_revision = '519b66176c0c'

from alembic import op


def upgrade():
    op.create_index('idx_completed_date', 'requests', ['completed_date'])


def downgrade():
    op.drop_index('idx_completed_date', 'requests')
