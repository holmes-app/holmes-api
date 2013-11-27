"""Page table indexes for next job

Revision ID: 10e3ffb42fc9
Revises: 34bd7155169
Create Date: 2013-11-27 15:20:16.940698

"""

# revision identifiers, used by Alembic.
revision = '10e3ffb42fc9'
down_revision = '34bd7155169'

from alembic import op


def upgrade():
    op.create_index('idx_pages_last_review_date', 'pages', ['last_review_started_date'])
    op.create_index('idx_pages_created_date', 'pages', ['created_date'])


def downgrade():
    op.drop_index('idx_pages_last_review_date', 'pages')
    op.drop_index('idx_pages_created_date', 'pages')
