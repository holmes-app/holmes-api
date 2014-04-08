"""added index for last_ping

Revision ID: 379d301c24ed
Revises: 2932df901655
Create Date: 2014-04-08 10:07:57.167665

"""

# revision identifiers, used by Alembic.
revision = '379d301c24ed'
down_revision = '2932df901655'

from alembic import op


def upgrade():
    op.create_index('idx_last_ping', 'workers', ['last_ping'])


def downgrade():
    op.drop_index('idx_last_ping', 'workers')
