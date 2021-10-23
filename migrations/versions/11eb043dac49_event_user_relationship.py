"""event_user relationship

Revision ID: 11eb043dac49
Revises: 48f7228d3947
Create Date: 2021-09-17 17:26:53.738315

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11eb043dac49'
down_revision = '48f7228d3947'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('users_events_users_id_fkey', 'users_events', type_='foreignkey')
    op.drop_constraint('users_events_events_id_fkey', 'users_events', type_='foreignkey')
    op.create_foreign_key(None, 'users_events', 'events', ['events_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'users_events', 'users', ['users_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users_events', type_='foreignkey')
    op.drop_constraint(None, 'users_events', type_='foreignkey')
    op.create_foreign_key('users_events_events_id_fkey', 'users_events', 'events', ['events_id'], ['id'])
    op.create_foreign_key('users_events_users_id_fkey', 'users_events', 'users', ['users_id'], ['id'])
    # ### end Alembic commands ###