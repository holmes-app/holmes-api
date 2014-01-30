"""Create some requests indexes

Revision ID: d8f500d9168
Revises: 234e746c4c28
Create Date: 2014-01-30 15:00:25.371123

"""

# revision identifiers, used by Alembic.
revision = 'd8f500d9168'
down_revision = '234e746c4c28'

from alembic import op


def upgrade():
    op.create_index(
        'idx_domain_status_code',
        'requests',
        ['domain_name', 'status_code']
    )


def downgrade():
    op.drop_index('idx_domain_status_code', 'requests')
