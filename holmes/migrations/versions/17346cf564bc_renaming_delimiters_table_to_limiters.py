"""Renaming delimiters table to limiters

Revision ID: 17346cf564bc
Revises: 4d45dd3d8ce5
Create Date: 2014-03-07 14:45:27.909631

"""

# revision identifiers, used by Alembic.
revision = '17346cf564bc'
down_revision = '4d45dd3d8ce5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.rename_table('delimiters', 'limiters')


def downgrade():
    op.rename_table('limiters', 'delimiters')
