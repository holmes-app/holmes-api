"""create delimiter table

Revision ID: 43ce6999f48e
Revises: 56e5b86b4b40
Create Date: 2014-02-10 18:27:15.111090

"""

# revision identifiers, used by Alembic.
revision = '43ce6999f48e'
down_revision = '37881a97d680'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'delimiters',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('url_hash', sa.String(128), nullable=False),
        sa.Column('value', sa.Integer, nullable=False, server_default='1')
    )

    op.create_index('idx_url_hash', 'delimiters', ['url_hash'])


def downgrade():
    op.drop_index('idx_url_hash', 'delimiters')
    op.drop_table('delimiters')

