"""create violation table

Revision ID: 3283f8a20fc9
Revises: 52988f72b077
Create Date: 2013-11-13 11:36:56.729207

"""

# revision identifiers, used by Alembic.
revision = '3283f8a20fc9'
down_revision = '52988f72b077'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'violations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(2000), nullable=False),
        sa.Column('description', sa.String(2000), nullable=False),
        sa.Column('key', sa.String(2000), nullable=False),
        sa.Column('points', sa.Integer, nullable=False),
        sa.Column('review_id', sa.Integer),
    )

    op.create_foreign_key(
        "fk_violation_review", "violations",
        "reviews", ["review_id"], ["id"]
    )


def downgrade():
    op.drop_constraint('fk_violation_review', 'violations', type_="foreignkey")
    op.drop_table('violations')
