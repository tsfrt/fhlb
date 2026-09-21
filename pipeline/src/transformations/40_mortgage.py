"""Mortgage & MPF domain — a genuine three-hop chain.

Edges: members -> mortgage_originations -> mpf_loans -> mpf_servicing_monthly.
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


@mv(name="mortgage_originations", comment=g.COMMENTS["mortgage_originations"]["table"])
def mortgage_originations():
    base = g.build(spark, g.gen_mortgage_originations())
    base = g.edge(spark, base, "members", "member_id")
    return g.finalize(base, "mortgage_originations")


@mv(name="mpf_loans", comment=g.COMMENTS["mpf_loans"]["table"])
def mpf_loans():
    base = g.build(spark, g.gen_mpf_loans())
    base = g.edge(spark, base, "mortgage_originations", "member_id")
    return g.finalize(base, "mpf_loans")


@mv(name="mpf_servicing_monthly", comment=g.COMMENTS["mpf_servicing_monthly"]["table"])
def mpf_servicing_monthly():
    base = g.build(spark, g.gen_mpf_servicing_monthly())
    base = g.edge(spark, base, "mpf_loans", "loan_id")
    return g.finalize(base, "mpf_servicing_monthly")
