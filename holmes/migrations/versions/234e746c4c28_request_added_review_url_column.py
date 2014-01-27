"""Request: Added review_url column

Revision ID: 234e746c4c28
Revises: 22bc83869dbe
Create Date: 2014-01-27 14:41:11.003174

"""

# revision identifiers, used by Alembic.
revision = '234e746c4c28'
down_revision = '22bc83869dbe'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'requests',
        sa.Column('review_url', sa.Text, nullable=False)
    )


def downgrade():
    op.drop_column('requests', 'review_url')
