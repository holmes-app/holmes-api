"""add last_review column to pages table

Revision ID: 1a316b08d134
Revises: 3283f8a20fc9
Create Date: 2013-11-13 15:37:58.838122

"""

# revision identifiers, used by Alembic.
revision = '1a316b08d134'
down_revision = '3283f8a20fc9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'pages',
        sa.Column('last_review_id', sa.Integer)
    )

    op.create_foreign_key(
        "fk_page_last_review", "pages",
        "reviews", ["last_review_id"], ["id"]
    )


def downgrade():
    op.drop_constraint('fk_page_last_review', 'pages', type_='foreignkey')
    op.drop_column('pages', 'last_review_id')
