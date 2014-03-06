"""added domain_id in violations table

Revision ID: 49d09b3d2801
Revises: 43ce6999f48e
Create Date: 2014-02-20 15:33:25.850731

"""

# revision identifiers, used by Alembic.
revision = '49d09b3d2801'
down_revision = '43ce6999f48e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('violations', sa.Column('domain_id', sa.Integer, nullable=True))

    connection = op.get_bind()
    connection.execute('UPDATE violations AS viol SET viol.domain_id = (SELECT rev.domain_id FROM reviews AS rev WHERE rev.id = viol.review_id)')

    op.alter_column('violations', 'domain_id', type_=sa.Integer, nullable=False)

    op.create_foreign_key(
        'fk_violation_domain', 'violations',
        'domains', ['domain_id'], ['id']
    )


def downgrade():
    op.drop_constraint('fk_violation_domain', 'violations', type_='foreignkey')
    op.drop_column('violations', 'domain_id')
