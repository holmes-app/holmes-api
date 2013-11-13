"""create domains table

Revision ID: 34a477a7f285
Revises: None
Create Date: 2013-11-13 09:49:16.883664

"""

# revision identifiers, used by Alembic.
revision = '34a477a7f285'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'domains',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('name', sa.String(2000), nullable=False),
    )


def downgrade():
    op.drop_table('domains')
