"""Users: email is unique

Revision ID: 4b96dd9974bb
Revises: 1d98f72f9d10
Create Date: 2014-03-14 14:40:26.069119

"""

# revision identifiers, used by Alembic.
revision = '4b96dd9974bb'
down_revision = '1d98f72f9d10'

from alembic import op


def upgrade():
    op.drop_index('idx_email', 'users')
    op.create_unique_constraint("uk_email", "users", ["email"])


def downgrade():
    op.create_index('idx_email', 'users', ['email'])
    op.drop_constraint('uk_email', 'users', type_='unique')
