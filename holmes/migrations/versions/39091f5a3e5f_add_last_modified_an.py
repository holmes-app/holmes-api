"""add last_modified and expires to pages

Revision ID: 39091f5a3e5f
Revises: 4ff6c7ad84c6
Create Date: 2013-11-28 23:42:57.692382

"""

# revision identifiers, used by Alembic.
revision = '39091f5a3e5f'
down_revision = '4ff6c7ad84c6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'pages',
        sa.Column('last_modified', sa.DateTime, nullable=True)
    )

    op.add_column(
        'pages',
        sa.Column('expires', sa.DateTime, nullable=True)
    )


def downgrade():
    op.drop_column('pages', 'last_modified')
    op.drop_column('pages', 'expires')
