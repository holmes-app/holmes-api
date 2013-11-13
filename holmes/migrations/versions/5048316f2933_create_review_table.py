"""create review table

Revision ID: 5048316f2933
Revises: 2cb79bf80b46
Create Date: 2013-11-13 10:39:50.428863

"""

# revision identifiers, used by Alembic.
revision = '5048316f2933'
down_revision = '2cb79bf80b46'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('is_active', sa.Boolean, default=False, nullable=False),
        sa.Column('is_complete', sa.Boolean, default=False, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('created_date', sa.DateTime, nullable=False),
        sa.Column('completed_date', sa.DateTime, nullable=True),
        sa.Column('last_review_started_date', sa.DateTime, nullable=True),
        sa.Column('last_review_started_date', sa.DateTime, nullable=True),
        sa.Column('failure_message', sa.String(2000), nullable=True),
        sa.Column('domain_id', sa.Integer),
        sa.Column('page_id', sa.Integer),
    )

    op.create_foreign_key(
        "fk_review_domain", "reviews",
        "domains", ["domain_id"], ["id"]
    )

    op.create_foreign_key(
        "fk_review_page", "reviews",
        "pages", ["page_id"], ["id"]
    )


def downgrade():
    op.drop_constraint('fk_review_domain', 'reviews', type_="foreignkey")
    op.drop_constraint('fk_review_page', 'reviews', type_="foreignkey")
    op.drop_table('reviews')
