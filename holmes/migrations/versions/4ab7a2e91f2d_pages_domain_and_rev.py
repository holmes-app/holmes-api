"""Pages, Domain and Review indexes for getting by uuid

Revision ID: 4ab7a2e91f2d
Revises: 5edcaddd6c9
Create Date: 2013-11-27 15:36:05.865518

"""

# revision identifiers, used by Alembic.
revision = '4ab7a2e91f2d'
down_revision = '5edcaddd6c9'

from alembic import op


def upgrade():
    op.create_index('idx_pages_uuid', 'pages', ['uuid'])
    op.create_index('idx_reviews_uuid', 'reviews', ['uuid'])


def downgrade():
    op.drop_index('idx_pages_uuid', 'pages')
    op.drop_index('idx_reviews_uuid', 'reviews')
