"""create facts table

Revision ID: 52988f72b077
Revises: 5048316f2933
Create Date: 2013-11-13 11:15:00.873936

"""

# revision identifiers, used by Alembic.
revision = '52988f72b077'
down_revision = '5048316f2933'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'facts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(2000), nullable=False),
        sa.Column('key', sa.String(2000), nullable=False),
        sa.Column('unit', sa.String(2000), nullable=False),
        sa.Column('value', sa.String(4000), nullable=False),
        sa.Column('review_id', sa.Integer),
    )

    op.create_foreign_key(
        "fk_fact_review", "facts",
        "reviews", ["review_id"], ["id"]
    )


def downgrade():
    op.drop_constraint('fk_fact_review', 'facts', type_="foreignkey")
    op.drop_table('facts')
