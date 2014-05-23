"""Create DomainsViolationsPrefs table

Revision ID: 2620096d8dd2
Revises: 2901a4935e21
Create Date: 2014-05-23 15:42:29.172112

"""

# revision identifiers, used by Alembic.
revision = '2620096d8dd2'
down_revision = '2901a4935e21'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'domains_violations_prefs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('domain_id', sa.Integer, nullable=False),
        sa.Column('key_id', sa.Integer, nullable=False),
        sa.Column('value', sa.Text)
    )

    op.create_foreign_key(
        "fk_domain", "domains_violations_prefs",
        "domains", ["domain_id"], ["id"]
    )

    op.create_foreign_key(
        "fk_key", "domains_violations_prefs",
        "keys", ["key_id"], ["id"]
    )

    op.create_unique_constraint(
        'uk_domain_key',
        'domains_violations_prefs',
        ["key_id", 'domain_id']
    )


def downgrade():
    op.drop_constraint('fk_domain', 'domains_violations_prefs', type_="foreignkey")
    op.drop_constraint('fk_key', 'domains_violations_prefs', type_="foreignkey")
    op.drop_constraint('uk_domain_key', 'domains_violations_prefs', type_='unique')
    op.drop_table('domains_violations_prefs')
