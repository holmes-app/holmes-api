"""Domain url index

Revision ID: 4260bbc20569
Revises: 4ab7a2e91f2d
Create Date: 2013-11-27 15:48:59.834199

"""

# revision identifiers, used by Alembic.
revision = '4260bbc20569'
down_revision = '4ab7a2e91f2d'

from alembic import op


def upgrade():
    op.execute('CREATE INDEX idx_domains_url on domains (url(220))')


def downgrade():
    op.drop_index('idx_domains_url', 'domains')
