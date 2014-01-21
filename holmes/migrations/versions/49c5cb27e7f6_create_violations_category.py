"""create violations category

Revision ID: 49c5cb27e7f6
Revises: 7fef2bae291
Create Date: 2014-01-21 19:46:14.259462

"""

# revision identifiers, used by Alembic.
revision = '49c5cb27e7f6'
down_revision = '7fef2bae291'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'keys_category',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
    )

    op.add_column(
        'keys',
        sa.Column('category_id', sa.Integer),
    )

    op.create_foreign_key(
        "fk_keys_category", "keys",
        "keys_category", ["category_id"], ["id"]
    )


def downgrade():
    op.drop_constraint(
        'fk_keys_category',
        'keys',
        type_="foreignkey"
    )

    op.drop_column('keys', 'category_id')
    op.drop_table('keys_category')
