"""Add locale field in User table

Revision ID: 5592365e4624
Revises: 47fac4be8ca7
Create Date: 2014-07-15 16:54:18.394370

"""

# revision identifiers, used by Alembic.
revision = '5592365e4624'
down_revision = '47fac4be8ca7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'users',
        sa.Column('locale', type_=sa.String(10))
    )


def downgrade():
    op.drop_column('users', 'locale')
