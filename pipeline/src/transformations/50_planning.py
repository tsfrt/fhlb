"""Financial-planning domain — actuals vs plan roots."""

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


@mv(name="financials_actual_vs_forecast", comment=g.COMMENTS["financials_actual_vs_forecast"]["table"])
def financials_actual_vs_forecast():
    return g.finalize(g.build(spark, g.gen_financials_actual_vs_forecast()), "financials_actual_vs_forecast")


@mv(name="vendor_spend", comment=g.COMMENTS["vendor_spend"]["table"])
def vendor_spend():
    return g.finalize(g.build(spark, g.gen_vendor_spend()), "vendor_spend")


@mv(name="capital_plan", comment=g.COMMENTS["capital_plan"]["table"])
def capital_plan():
    return g.finalize(g.build(spark, g.gen_capital_plan()), "capital_plan")
