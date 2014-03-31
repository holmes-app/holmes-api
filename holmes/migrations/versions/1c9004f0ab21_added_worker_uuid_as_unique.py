"""Added worker uuid as unique

Revision ID: 1c9004f0ab21
Revises: 7f4a3b8c55d
Create Date: 2014-03-31 18:37:10.921215

"""

# revision identifiers, used by Alembic.
revision = '1c9004f0ab21'
down_revision = '7f4a3b8c55d'

from alembic import op


def upgrade():
    op.create_unique_constraint('uk_uuid', 'workers', ['uuid'])


def downgrade():
    op.drop_constraint('uk_uuid', 'workers', type_='unique')
