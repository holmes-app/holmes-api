"""Violation: value can be null

Revision ID: 2f69133b476d
Revises: 1e071953a65d
Create Date: 2013-12-06 16:16:49.228679

"""

# revision identifiers, used by Alembic.
revision = '2f69133b476d'
down_revision = '1e071953a65d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('violations', 'value',  type_=sa.Text, nullable=True)


def downgrade():
    op.alter_column('violations', 'value',  type_=sa.Text, nullable=False)
