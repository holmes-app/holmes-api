"""change_keys_of_facters_and_violations_to_separated_table

Revision ID: 4cf3e398a81f
Revises: 21087e990aa8
Create Date: 2013-12-04 17:42:02.709200

"""

# revision identifiers, used by Alembic.
revision = '4cf3e398a81f'
down_revision = '21087e990aa8'

from alembic import op
import sqlalchemy as sa

def upgrade():
    connection = op.get_bind()

    op.create_table(
        'keys',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(2000), nullable=False)
    )

    op.add_column('facts', sa.Column('key_id', sa.Integer, nullable=False))
    op.add_column('violations', sa.Column('key_id', sa.Integer, nullable=False))

    keys = set()

    for values in connection.execute('SELECT DISTINCT(`key`) FROM violations;'):
        keys.add(values[0])

    for values in connection.execute('SELECT DISTINCT(`key`) FROM facts;'):
        keys.add(values[0])

    if keys:
        connection.execute('INSERT INTO `keys` (`name`) VALUES {0}'.format(', '.join(('(\'{0}\')'.format(key) for key in keys))))

    for values in connection.execute('SELECT id, `name` FROM `keys`'):
        connection.execute('UPDATE facts SET key_id = \'{0}\' WHERE `key` = \'{1}\''.format(*values))
        connection.execute('UPDATE violations SET key_id = \'{0}\' WHERE `key` = \'{1}\''.format(*values))

    op.create_foreign_key(
        "fk_key_fact", 'facts',
        "keys", ["key_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_key_violation", 'violations',
        "keys", ["key_id"], ["id"]
    )

    op.drop_column('facts', 'key')
    op.drop_column('violations', 'key')


def downgrade():
    connection = op.get_bind()

    op.add_column('facts', sa.Column('key', sa.String(2000)))
    op.add_column('violations', sa.Column('key', sa.String(2000)))

    for values in connection.execute('SELECT id, `name` FROM `keys`'):
        id_, key = values
        connection.execute('UPDATE facts SET `key` = \'{0}\' WHERE key_id = \'{1}\''.format(key, id_))
        connection.execute('UPDATE violations SET `key` = \'{0}\' WHERE key_id = \'{1}\''.format(key, id_))

    op.drop_constraint('fk_key_fact', 'facts', type_='foreignkey')
    op.drop_column('facts', 'key_id')

    op.drop_constraint('fk_key_violation', 'violations', type_='foreignkey')
    op.drop_column('violations', 'key_id')

    op.drop_table('keys')
