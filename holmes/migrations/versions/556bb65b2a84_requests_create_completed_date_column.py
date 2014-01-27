"""requests: create completed_date column

Revision ID: 556bb65b2a84
Revises: 59ceb7a18e80
Create Date: 2014-01-27 13:43:03.762366

"""

# revision identifiers, used by Alembic.
revision = '556bb65b2a84'
down_revision = '59ceb7a18e80'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'requests',
        sa.Column('completed_date', sa.Date, nullable=False)
    )


def downgrade():
    op.drop_column('requests', 'completed_date')
