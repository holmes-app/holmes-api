"""add a flag for review active

Revision ID: 4d45dd3d8ce5
Revises: 49d09b3d2801
Create Date: 2014-02-26 16:29:54.507710

"""

# revision identifiers, used by Alembic.
revision = '4d45dd3d8ce5'
down_revision = '49d09b3d2801'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'violations',
        sa.Column('review_is_active', sa.Integer, nullable=False, server_default='1')
    )

    connection = op.get_bind()
    connection.execute('''UPDATE violations
        SET review_is_active = 0
        WHERE review_id IN (SELECT id FROM reviews WHERE is_active = 0)''')

    op.create_index(
        'idx_key_domain_review_active',
        'violations',
        ['key_id', 'domain_id', 'review_is_active'])


def downgrade():
    op.drop_index('idx_key_domain_review_active', 'violations')
    op.drop_column('violations', 'review_is_active')
