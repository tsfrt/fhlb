"""Collateral domain.

Edge: advance_daily_balances -> pledged_collateral (collateral is sized against
the members that carry advances, so the graph shows advances feeding collateral).
"""

import os
import sys

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    from pyspark import pipelines as dp
    mv = dp.materialized_view
except ImportError:
    import dlt as dp
    mv = dp.table

import _common as g


@mv(name="pledged_collateral", comment=g.COMMENTS["pledged_collateral"]["table"])
def pledged_collateral():
    base = g.build(spark, g.gen_pledged_collateral())
    base = g.edge(spark, base, "advance_daily_balances", "member_id")
    return g.finalize(base, "pledged_collateral")


@mv(name="collateral_reviews", comment=g.COMMENTS["collateral_reviews"]["table"])
def collateral_reviews():
    return g.finalize(g.build(spark, g.gen_collateral_reviews()), "collateral_reviews")
