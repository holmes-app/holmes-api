"""drop workers table

Revision ID: 519b66176c0c
Revises: 379d301c24ed
Create Date: 2014-04-10 15:53:05.866376

"""

# revision identifiers, used by Alembic.
revision = '519b66176c0c'
down_revision = '379d301c24ed'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint('uk_uuid', 'workers', type_='unique')
    op.drop_index('idx_last_ping', 'workers')
    op.drop_table('workers')


def downgrade():
    op.create_table(
        'workers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('last_ping', sa.DateTime, nullable=False),
        sa.Column('current_url', sa.Text, nullable=True)
    )

    op.create_unique_constraint('uk_uuid', 'workers', ['uuid'])
    op.create_index('idx_last_ping', 'workers', ['last_ping'])
