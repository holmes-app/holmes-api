"""Added index for name in keys_category

Revision ID: 2901a4935e21
Revises: 2db70040b01b
Create Date: 2014-05-12 19:16:34.562972

"""

# revision identifiers, used by Alembic.
revision = '2901a4935e21'
down_revision = '2db70040b01b'

from alembic import op


def upgrade():
    op.create_unique_constraint('uk_name', 'keys_category', ['name'])


def downgrade():
    op.drop_constraint('uk_name', 'keys_category', type_='unique')
