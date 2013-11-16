"""change value column type

Revision ID: f851ec9af09
Revises: 178c6db7516
Create Date: 2013-11-16 13:20:14.099934

"""

# revision identifiers, used by Alembic.
revision = 'f851ec9af09'
down_revision = '178c6db7516'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('facts', 'value', type_=sa.Text, nullable=False)


def downgrade():
    op.alter_column('facts', 'value', type_=sa.String(4000), nullable=False)
