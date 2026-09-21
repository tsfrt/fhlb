"""Governance & operations domain — the exam-ready backbone.

Edges: ops_source_systems -> ops_data_quality_exceptions, ops_column_lineage;
members -> ops_access_events; eadvantage_activity -> ops_gl_reconciliation.
The rest (BI refresh, metric recon, examiner requests, pipeline cost, AI content
sources) are independent operational logs.
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


@mv(name="ops_data_quality_exceptions", comment=g.COMMENTS["ops_data_quality_exceptions"]["table"])
def ops_data_quality_exceptions():
    base = g.build(spark, g.gen_ops_data_quality_exceptions())
    base = g.edge(spark, base, "ops_source_systems", "source_system_id")
    return g.finalize(base, "ops_data_quality_exceptions")


@mv(name="ops_column_lineage", comment=g.COMMENTS["ops_column_lineage"]["table"])
def ops_column_lineage():
    base = g.build(spark, g.gen_ops_column_lineage())
    base = g.edge(spark, base, "ops_source_systems", "source_system_id")
    return g.finalize(base, "ops_column_lineage")


@mv(name="ops_access_events", comment=g.COMMENTS["ops_access_events"]["table"])
def ops_access_events():
    base = g.build(spark, g.gen_ops_access_events())
    base = g.edge(spark, base, "members", "member_id")
    return g.finalize(base, "ops_access_events")


@mv(name="ops_gl_reconciliation", comment=g.COMMENTS["ops_gl_reconciliation"]["table"])
def ops_gl_reconciliation():
    base = g.build(spark, g.gen_ops_gl_reconciliation())
    base = g.edge(spark, base, "eadvantage_activity", "feed_name")
    return g.finalize(base, "ops_gl_reconciliation")


@mv(name="ops_bi_refresh", comment=g.COMMENTS["ops_bi_refresh"]["table"])
def ops_bi_refresh():
    return g.finalize(g.build(spark, g.gen_ops_bi_refresh()), "ops_bi_refresh")


@mv(name="ops_metric_reconciliation", comment=g.COMMENTS["ops_metric_reconciliation"]["table"])
def ops_metric_reconciliation():
    return g.finalize(g.build(spark, g.gen_ops_metric_reconciliation()), "ops_metric_reconciliation")


@mv(name="ops_examiner_requests", comment=g.COMMENTS["ops_examiner_requests"]["table"])
def ops_examiner_requests():
    return g.finalize(g.build(spark, g.gen_ops_examiner_requests()), "ops_examiner_requests")


@mv(name="ops_pipeline_cost", comment=g.COMMENTS["ops_pipeline_cost"]["table"])
def ops_pipeline_cost():
    return g.finalize(g.build(spark, g.gen_ops_pipeline_cost()), "ops_pipeline_cost")


@mv(name="ops_ai_content_sources", comment=g.COMMENTS["ops_ai_content_sources"]["table"])
def ops_ai_content_sources():
    return g.finalize(g.build(spark, g.gen_ops_ai_content_sources()), "ops_ai_content_sources")
