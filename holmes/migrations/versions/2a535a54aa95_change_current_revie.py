"""change current_review column in worker table to current_url

Revision ID: 2a535a54aa95
Revises: f851ec9af09
Create Date: 2013-11-18 15:05:07.519054

"""

# revision identifiers, used by Alembic.
revision = '2a535a54aa95'
down_revision = 'f851ec9af09'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'workers',
        sa.Column('current_url', sa.Text)
    )

    op.drop_constraint('fk_worker_current_review', 'workers', type_="foreignkey")
    op.drop_column('workers', 'current_review_id')


def downgrade():
    op.add_column(
        'workers',
        sa.Column('current_review_id', sa.Integer)
    )

    op.create_foreign_key(
        "fk_worker_current_review", "workers",
        "reviews", ["current_review_id"], ["id"]
    )

    op.drop_column('workers', 'current_url')
