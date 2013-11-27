"""Add last_review_date to page

Revision ID: 34bd7155169
Revises: 122a0b422e76
Create Date: 2013-11-27 15:16:23.976269

"""

# revision identifiers, used by Alembic.
revision = '34bd7155169'
down_revision = '122a0b422e76'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'pages',
        sa.Column('last_review_date', sa.DateTime, nullable=True)
    )


def downgrade():
    op.drop_column('pages', 'last_review_date')
