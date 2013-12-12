"""Key name must be unique

Revision ID: cc4091b07cb
Revises: 2f69133b476d
Create Date: 2013-12-12 11:23:55.314017

"""

# revision identifiers, used by Alembic.
revision = 'cc4091b07cb'
down_revision = '2f69133b476d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('keys', 'name', type_=sa.String(255))
    op.create_unique_constraint("uk_name", "keys", ["name"])


def downgrade():
    op.drop_constraint('uk_name', 'keys', type_='unique')
    op.alter_column('keys', 'name', type_=sa.String(2000))
