"""Create users_violations_prefs table

Revision ID: 47fac4be8ca7
Revises: 19ffab346000
Create Date: 2014-07-14 19:00:15.740884

"""

# revision identifiers, used by Alembic.
revision = '47fac4be8ca7'
down_revision = '19ffab346000'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'users_violations_prefs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('key_id', sa.Integer, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )

    op.create_unique_constraint(
        'uk_user_key',
        'users_violations_prefs',
        ['key_id', 'user_id']
    )

    op.create_foreign_key(
        'fk_user', 'users_violations_prefs',
        'users', ['user_id'], ['id']
    )

    op.create_foreign_key(
        'fk_key_id', 'users_violations_prefs',
        'keys', ['key_id'], ['id']
    )


def downgrade():
    op.drop_constraint('fk_user', 'users_violations_prefs', type_='foreignkey')
    op.drop_constraint('fk_key_id', 'users_violations_prefs', type_='foreignkey')
    op.drop_constraint('uk_user_key', 'users_violations_prefs', type_='unique')
    op.drop_table('users_violations_prefs')
