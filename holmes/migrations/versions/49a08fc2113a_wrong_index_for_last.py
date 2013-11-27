"""Wrong index for last_review_date

Revision ID: 49a08fc2113a
Revises: 3a3aa7483604
Create Date: 2013-11-27 17:53:25.879893

"""

# revision identifiers, used by Alembic.
revision = '49a08fc2113a'
down_revision = '3a3aa7483604'

from alembic import op


def upgrade():
    op.drop_index('idx_pages_last_review_date', 'pages')
    op.create_index('idx_pages_last_review_date', 'pages', ['last_review_date'])


def downgrade():
    op.drop_index('idx_pages_last_review_date', 'pages')
    op.create_index('idx_pages_last_review_date', 'pages', ['last_review_started_date'])
