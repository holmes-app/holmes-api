"""Added User.provider column

Revision ID: 19ffab346000
Revises: 2620096d8dd2
Create Date: 2014-07-02 11:54:19.472151

"""

# revision identifiers, used by Alembic.
revision = '19ffab346000'
down_revision = '2620096d8dd2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'users',
        sa.Column('provider', type_=sa.String(10), nullable=True)
    )


def downgrade():
    op.drop_column('users', 'provider')
