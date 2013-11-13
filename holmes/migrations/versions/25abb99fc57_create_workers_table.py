"""create workers table

Revision ID: 25abb99fc57
Revises: 1a316b08d134
Create Date: 2013-11-13 16:00:05.263655

"""

# revision identifiers, used by Alembic.
revision = '25abb99fc57'
down_revision = '1a316b08d134'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'workers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('last_ping', sa.DateTime, nullable=False),
        sa.Column('current_review_id', sa.Integer)
    )

    op.create_foreign_key(
        "fk_worker_current_review", "workers",
        "reviews", ["current_review_id"], ["id"]
    )


def downgrade():
    op.drop_constraint('fk_worker_current_review', 'workers', type_='foreignkey')
    op.drop_table('workers')
