"""add company_website (users) and screenshot_path (b2b_check_results)

Revision ID: ae3b9c2d7f4
Revises: 4c42b76b1482
Create Date: 2025-11-23 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae3b9c2d7f4'
down_revision = '4c42b76b1482'
branch_labels = None
depends_on = None


def upgrade():
    # Add company_website to users
    op.add_column('users', sa.Column('company_website', sa.String(length=255), nullable=True))

    # Add screenshot_path to b2b_check_results
    op.add_column('b2b_check_results', sa.Column('screenshot_path', sa.String(length=512), nullable=True))


def downgrade():
    # Remove columns on downgrade
    with op.batch_alter_table('b2b_check_results') as batch_op:
        batch_op.drop_column('screenshot_path')

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('company_website')
