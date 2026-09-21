"""Credit-risk domain — feeds the deployed Member Early-Warning model.

Edges: members -> member_credit_ratings, call_reports_quarterly;
ops_model_inventory -> member_credit_ratings (rating model provenance).
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


@mv(name="member_credit_ratings", comment=g.COMMENTS["member_credit_ratings"]["table"])
def member_credit_ratings():
    base = g.build(spark, g.gen_member_credit_ratings())
    base = g.edge(spark, base, "members", "member_id")
    base = g.edge(spark, base, "ops_model_inventory", "rating_model_id", upstream_key="model_id")
    return g.finalize(base, "member_credit_ratings")


@mv(name="call_reports_quarterly", comment=g.COMMENTS["call_reports_quarterly"]["table"])
def call_reports_quarterly():
    base = g.build(spark, g.gen_call_reports_quarterly())
    base = g.edge(spark, base, "members", "member_id")
    return g.finalize(base, "call_reports_quarterly")
