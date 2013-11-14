"""add domain, page url unique keys

Revision ID: 178c6db7516
Revises: 25abb99fc57
Create Date: 2013-11-14 16:53:36.719799

"""

# revision identifiers, used by Alembic.
revision = '178c6db7516'
down_revision = '25abb99fc57'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column(
        'pages',
        sa.Column('url_hash', type_=sa.String(128))
    )

    op.add_column(
        'domains',
        sa.Column('url_hash', type_=sa.String(128))
    )

    op.alter_column('domains', 'url', type_=sa.Text)
    op.alter_column('pages', 'url', type_=sa.Text)
    op.create_unique_constraint("uk_domain_url", "domains", ["url_hash"])
    op.create_unique_constraint("uk_page_url", "pages", ["url_hash"])


def downgrade():
    op.drop_constraint('uk_domain_url', 'domains', type_='unique')
    op.drop_constraint('uk_page_url', 'pages', type_='unique')
    op.alter_column('pages', 'url', type_=sa.String(2000))
    op.alter_column('domains', 'url', type_=sa.String(2000))
    op.drop_column('pages', 'url_hash')
    op.drop_column('domains', 'url_hash')
