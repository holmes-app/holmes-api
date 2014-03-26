"""Converting the value of violations and facts to BLOB

Revision ID: 155c6ce689ed
Revises: 1c9004f0ab21
Create Date: 2014-04-03 09:03:49.118969

"""

# revision identifiers, used by Alembic.
revision = '155c6ce689ed'
down_revision = '1c9004f0ab21'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('facts', 'value', type_=sa.BLOB(length=4294967295), nullable=False)
    op.alter_column('violations', 'value', type_=sa.BLOB(length=4294967295), nullable=False)


def downgrade():
    op.alter_column('facts', 'value', type_=sa.Text(length=4294967295), nullable=False)
    op.alter_column('violations', 'value', type_=sa.Text(length=4294967295), nullable=False)
