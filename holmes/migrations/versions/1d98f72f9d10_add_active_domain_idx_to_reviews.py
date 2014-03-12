"""add active,domain idx to reviews

Revision ID: 1d98f72f9d10
Revises: 17346cf564bc
Create Date: 2014-03-12 11:59:05.795869

"""

# revision identifiers, used by Alembic.
revision = '1d98f72f9d10'
down_revision = '17346cf564bc'

from alembic import op


def upgrade():
    op.create_index('idx_is_active_domain', 'reviews', ['is_active', 'domain_id'])


def downgrade():
    op.drop_index('idx_is_active_domain', 'reviews')
