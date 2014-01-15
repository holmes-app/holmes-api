"""Changing facts value to Longtext

Revision ID: 3412b4b8b24e
Revises: 4779cd2391f7
Create Date: 2014-01-15 15:19:06.258099

"""

# revision identifiers, used by Alembic.
revision = '3412b4b8b24e'
down_revision = '4779cd2391f7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('facts', 'value', type_=sa.Text(length=4294967295), nullable=False)


def downgrade():
    op.alter_column('facts', 'value', type_=sa.Text(), nullable=False)
