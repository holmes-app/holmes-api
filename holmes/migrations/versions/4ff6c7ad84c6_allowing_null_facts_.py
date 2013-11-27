"""Allowing null facts and violations

Revision ID: 4ff6c7ad84c6
Revises: 49a08fc2113a
Create Date: 2013-11-27 21:27:50.757008

"""

# revision identifiers, used by Alembic.
revision = '4ff6c7ad84c6'
down_revision = '49a08fc2113a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('facts', 'value', type_=sa.Text, nullable=True)


def downgrade():
    op.alter_column('facts', 'value', type_=sa.Text, nullable=False)
