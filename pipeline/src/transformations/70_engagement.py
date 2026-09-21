"""Member engagement domain.

Edge: members -> eadvantage_activity.
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


@mv(name="eadvantage_activity", comment=g.COMMENTS["eadvantage_activity"]["table"])
def eadvantage_activity():
    base = g.build(spark, g.gen_eadvantage_activity())
    base = g.edge(spark, base, "members", "member_id")
    return g.finalize(base, "eadvantage_activity")
