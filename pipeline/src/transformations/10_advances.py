"""Advances & pricing domain — the Bank's core mission asset.

Edges: members -> advance_daily_balances, letters_of_credit; members(member_type)
-> advance_forecast_quarterly(member_segment).
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


@mv(name="advance_daily_balances", comment=g.COMMENTS["advance_daily_balances"]["table"])
def advance_daily_balances():
    base = g.build(spark, g.gen_advance_daily_balances())
    base = g.edge(spark, base, "members", "member_id")
    return g.finalize(base, "advance_daily_balances")


@mv(name="advance_forecast_quarterly", comment=g.COMMENTS["advance_forecast_quarterly"]["table"])
def advance_forecast_quarterly():
    base = g.build(spark, g.gen_advance_forecast_quarterly())
    base = g.edge(spark, base, "members", "member_segment", upstream_key="member_type")
    return g.finalize(base, "advance_forecast_quarterly")


@mv(name="letters_of_credit", comment=g.COMMENTS["letters_of_credit"]["table"])
def letters_of_credit():
    base = g.build(spark, g.gen_letters_of_credit())
    base = g.edge(spark, base, "members", "member_id")
    return g.finalize(base, "letters_of_credit")
