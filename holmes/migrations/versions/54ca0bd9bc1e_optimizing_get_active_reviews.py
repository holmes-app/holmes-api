"""Refactoring get_active_reviews

Revision ID: 54ca0bd9bc1e
Revises: cc4091b07cb
Create Date: 2014-01-03 15:58:28.836246

"""

# revision identifiers, used by Alembic.
revision = '54ca0bd9bc1e'
down_revision = 'cc4091b07cb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('pages', sa.Column('violations_count', sa.Integer, server_default='0', nullable=False))
    op.create_index('idx_violations_count', 'pages', ['violations_count'])

    op.add_column('pages', sa.Column('last_review_uuid', sa.String(36), nullable=True))
    op.create_index('idx_last_review_uuid', 'pages', ['last_review_uuid'])

    connection = op.get_bind()
    query = (
        'SELECT count(violations.id) AS violations_count, reviews.uuid, reviews.page_id '
        'FROM reviews LEFT OUTER JOIN violations ON violations.review_id = reviews.id '
        'WHERE reviews.is_active = 1 '
        'GROUP BY reviews.id'
    )

    for values in connection.execute(query):
        update = (
            'UPDATE pages '
            'SET violations_count = \'{0}\', last_review_uuid = \'{1}\' '
            'WHERE `id` = \'{2}\''.format(*values)
        )
        connection.execute(update)


def downgrade():
    op.drop_index('idx_violations_count', 'pages')
    op.drop_column('pages', 'violations_count')

    op.drop_index('idx_last_review_uuid', 'pages')
    op.drop_column('pages', 'last_review_uuid')
