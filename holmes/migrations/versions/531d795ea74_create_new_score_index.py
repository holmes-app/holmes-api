"""Create new score index

Revision ID: 531d795ea74
Revises: 3412b4b8b24e
Create Date: 2014-01-16 16:51:54.447201

"""

# revision identifiers, used by Alembic.
revision = '531d795ea74'
down_revision = '3412b4b8b24e'

from alembic import op


def upgrade():
    op.drop_index('idx_pages_score', 'pages')

    connection = op.get_bind()
    connection.execute('CREATE index idx_last_review_date_score on pages(last_review_date, score DESC)')


def downgrade():
    op.drop_index('idx_last_review_date_score', 'pages')
    op.create_index('idx_pages_score', 'pages', ['score'])
