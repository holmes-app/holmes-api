"""create AOPIC score and lambda page

Revision ID: 4779cd2391f7
Revises: 368929fa3075
Create Date: 2014-01-14 19:30:17.565805

"""

# revision identifiers, used by Alembic.
revision = '4779cd2391f7'
down_revision = '368929fa3075'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'pages',
        sa.Column('score', sa.Float, nullable=False, server_default=sa.text('0.0'))
    )

    op.create_table(
        'settings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('lambda_score', sa.Float, server_default=sa.text('0.0'), nullable=False)
    )

    connection = op.get_bind()
    connection.execute('INSERT INTO settings(lambda_score) VALUES(0.0)')

    op.create_index('idx_pages_score', 'pages', ['score'])


def downgrade():
    op.drop_table('settings')

    op.drop_index('idx_pages_score', 'pages')
    op.drop_column('pages', 'score')
