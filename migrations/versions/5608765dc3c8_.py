"""empty message

Revision ID: 5608765dc3c8
Revises: 80421895c9c1
Create Date: 2020-03-18 02:55:44.525842

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '5608765dc3c8'
down_revision = '80421895c9c1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('crypt', sqlalchemy_utils.types.encrypted.encrypted_type.EncryptedType(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'crypt')
    # ### end Alembic commands ###
