"""Reference domain — the roots of the FHLB data model graph.

members is the hub every other domain joins back to; ops_source_systems and
ops_model_inventory seed the governance and credit-rating lineage.
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
except ImportError:  # older runtimes expose the legacy DLT module
    import dlt as dp
    mv = dp.table

import _common as g


@mv(name="members", comment=g.COMMENTS["members"]["table"])
def members():
    return g.finalize(g.build(spark, g.gen_members()), "members")


@mv(name="eligible_nonmembers", comment=g.COMMENTS["eligible_nonmembers"]["table"])
def eligible_nonmembers():
    return g.finalize(g.build(spark, g.gen_eligible_nonmembers()), "eligible_nonmembers")


@mv(name="ops_source_systems", comment=g.COMMENTS["ops_source_systems"]["table"])
def ops_source_systems():
    return g.finalize(g.build(spark, g.gen_ops_source_systems()), "ops_source_systems")


@mv(name="ops_model_inventory", comment=g.COMMENTS["ops_model_inventory"]["table"])
def ops_model_inventory():
    return g.finalize(g.build(spark, g.gen_ops_model_inventory()), "ops_model_inventory")
