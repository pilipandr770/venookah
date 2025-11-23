"""merge heads f08cac5b5d1e and ae3b9c2d7f4

Revision ID: merge_f08cac_ae3b9c2d7f4
Revises: f08cac5b5d1e, ae3b9c2d7f4
Create Date: 2025-11-23 17:45:00.000000

This is an empty merge migration to combine two heads created during development.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_f08cac_ae3b9c2d7f4'
down_revision = ('f08cac5b5d1e', 'ae3b9c2d7f4')
branch_labels = None
depends_on = None


def upgrade():
    # merge-only migration; no DB operations
    pass


def downgrade():
    # nothing to downgrade
    pass
