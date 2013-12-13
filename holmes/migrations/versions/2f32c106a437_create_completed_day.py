"""create completed_day column

Revision ID: 2f32c106a437
Revises: 4cf3e398a81f
Create Date: 2013-12-05 14:09:40.756413

"""

# revision identifiers, used by Alembic.
revision = '2f32c106a437'
down_revision = '4cf3e398a81f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('reviews', sa.Column('completed_day', sa.Date, nullable=True))

    connection = op.get_bind()
    connection.execute('UPDATE reviews set completed_day=DATE(completed_date) where is_complete=1;')


def downgrade():
    op.drop_column('reviews', 'completed_day')
