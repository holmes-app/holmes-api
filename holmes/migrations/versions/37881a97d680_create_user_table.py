"""create user table

Revision ID: 37881a97d680
Revises: d8f500d9168
Create Date: 2014-02-10 15:52:50.366173

"""

# revision identifiers, used by Alembic.
revision = '37881a97d680'
down_revision = 'd8f500d9168'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('fullname', sa.String(200), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('last_login', sa.DateTime, nullable=True),
        sa.Column(
            'is_superuser',
            sa.Boolean,
            nullable=False,
            server_default='0'
        )
    )

    op.create_index('idx_email', 'users', ['email'])


def downgrade():
    op.drop_index('idx_email', 'users')
    op.drop_table('users')
