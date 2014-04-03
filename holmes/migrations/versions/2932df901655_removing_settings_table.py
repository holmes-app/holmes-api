"""Removing settings table

Revision ID: 2932df901655
Revises: 155c6ce689ed
Create Date: 2014-04-03 10:45:09.592592

"""

# revision identifiers, used by Alembic.
revision = '2932df901655'
down_revision = '155c6ce689ed'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('settings')


def downgrade():
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'lambda_score',
            sa.Float,
            server_default=sa.text('0.0'),
            nullable=False
        )
    )

    connection = op.get_bind()
    connection.execute('INSERT INTO settings(lambda_score) VALUES(0.0)')
