"""domain_is_active

Revision ID: 7fef2bae291
Revises: 531d795ea74
Create Date: 2014-01-17 18:44:04.637011

"""

# revision identifiers, used by Alembic.
revision = '7fef2bae291'
down_revision = '531d795ea74'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'domains',
        sa.Column('is_active', sa.Boolean, default=True, nullable=False)
    )
    connection = op.get_bind()
    connection.execute('UPDATE domains set is_active=1;')


def downgrade():
    op.drop_column('domains', 'is_active')
