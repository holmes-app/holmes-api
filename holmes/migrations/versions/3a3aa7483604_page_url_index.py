"""Page url index

Revision ID: 3a3aa7483604
Revises: 4260bbc20569
Create Date: 2013-11-27 15:58:18.367398

"""

# revision identifiers, used by Alembic.
revision = '3a3aa7483604'
down_revision = '4260bbc20569'

from alembic import op


def upgrade():
    op.execute('CREATE INDEX idx_pages_url on pages (url(220))')


def downgrade():
    op.drop_index('idx_pages_url', 'pages')
