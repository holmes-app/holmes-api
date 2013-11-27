"""Review table indexes for active reviews

Revision ID: 5edcaddd6c9
Revises: 10e3ffb42fc9
Create Date: 2013-11-27 15:28:20.189260

"""

# revision identifiers, used by Alembic.
revision = '5edcaddd6c9'
down_revision = '10e3ffb42fc9'

from alembic import op


def upgrade():
    op.create_index('idx_reviews_is_active', 'reviews', ['is_active'])
    op.create_index('idx_reviews_completed_date', 'reviews', ['completed_date'])


def downgrade():
    op.drop_index('idx_reviews_is_active', 'reviews')
    op.drop_index('idx_reviews_completed_date', 'reviews')
