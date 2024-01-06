"""Added is_cancelled atribute to gpu booking

Revision ID: 6824db27c6df
Revises: bf4411718ca3
Create Date: 2024-01-05 18:01:13.253607

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6824db27c6df'
down_revision = 'bf4411718ca3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Add the new columns
    with op.batch_alter_table('gpu_booking', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_cancelled', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        batch_op.add_column(sa.Column('cancelled_at', sa.DateTime(), nullable=True))
    
    # Update existing rows separately
    op.execute('UPDATE gpu_booking SET is_cancelled = false WHERE is_cancelled IS NULL')

    # ### end Alembic commands ###




def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('gpu_booking', schema=None) as batch_op:
        batch_op.drop_column('cancelled_at')
        batch_op.drop_column('is_cancelled')

    # ### end Alembic commands ###