"""change description column

Revision ID: 122a0b422e76
Revises: 2a535a54aa95
Create Date: 2013-11-20 11:25:09.363983

"""

# revision identifiers, used by Alembic.
revision = '122a0b422e76'
down_revision = '2a535a54aa95'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('violations', 'description', type_=sa.Text, nullable=False)


def downgrade():
    op.alter_column('violations', 'description', type_=sa.String(2000), nullable=False)
