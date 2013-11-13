"""create page table

Revision ID: 1fa4469fb63b
Revises: 34a477a7f285
Create Date: 2013-11-13 10:21:17.150033

"""

# revision identifiers, used by Alembic.
revision = '1fa4469fb63b'
down_revision = '34a477a7f285'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'pages',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('created_date', sa.DateTime, nullable=False),
        sa.Column('last_review_started_date', sa.DateTime, nullable=True),
        sa.Column('domain_id', sa.Integer)
    )

    op.create_foreign_key(
        "fk_page_domain", "pages",
        "domains", ["domain_id"], ["id"]
    )


def downgrade():
    op.drop_constraint('fk_page_domain', 'pages', type_="foreignkey")
    op.drop_table('pages')
