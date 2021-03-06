"""empty message

Revision ID: dca6e235628f
Revises:
Create Date: 2020-03-15 00:04:08.459880

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'dca6e235628f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('post_campaigns',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=True),
    sa.Column('campaign_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('processed_campaigns',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=True),
    sa.Column('campaign_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_constraint('posts_ibfk_2', 'posts', type_='foreignkey')
    op.drop_column('posts', 'processed')
    op.drop_column('posts', 'campaign_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('campaign_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.add_column('posts', sa.Column('processed', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.create_foreign_key('posts_ibfk_2', 'posts', 'campaigns', ['campaign_id'], ['id'], ondelete='SET NULL')
    op.drop_table('processed_campaigns')
    op.drop_table('post_campaigns')
    # ### end Alembic commands ###
