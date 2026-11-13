"""no negative values, historic goes up

Revision ID: 0a827e81bf1d
Revises: 00f64180cc3b
Create Date: 2026-11-13 12:00:00.000000

Written by hand: autogenerate does not detect CHECK changes.
    - entry_values: no negative values
    - badges: a historic badge always goes up, so only records can have tiers going down
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0a827e81bf1d'
down_revision: Union[str, Sequence[str], None] = '00f64180cc3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ASCENDING_TIERS = "0 < unlocked AND unlocked < bronze AND bronze < silver AND silver < gold AND gold < diamond"
DESCENDING_TIERS = "unlocked > bronze AND bronze > silver AND silver > gold AND gold > diamond AND diamond > 0"


def tiers_order(descending: str) -> str:
    """Tiers order CHECK, for the badges that go down."""
    return f"(({descending}) AND {DESCENDING_TIERS}) OR (NOT ({descending}) AND {ASCENDING_TIERS})"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(op.f('ck_entry_values_value_not_negative'), 'entry_values', "value >= 0")
    op.create_check_constraint(op.f('ck_badges_historic_goes_up'), 'badges', "kind <> 'historic' OR higher_is_better = true")
    op.drop_constraint(op.f('ck_badges_tiers_order'), 'badges', type_='check')
    op.create_check_constraint(op.f('ck_badges_tiers_order'), 'badges', tiers_order("kind = 'record' AND higher_is_better = false"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_badges_tiers_order'), 'badges', type_='check')
    op.create_check_constraint(op.f('ck_badges_tiers_order'), 'badges', tiers_order("kind IN ('historic', 'record') AND higher_is_better = false"))
    op.drop_constraint(op.f('ck_badges_historic_goes_up'), 'badges', type_='check')
    op.drop_constraint(op.f('ck_entry_values_value_not_negative'), 'entry_values', type_='check')
