"""Investments & funding domain — independent market/portfolio roots."""

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


@mv(name="market_rates_daily", comment=g.COMMENTS["market_rates_daily"]["table"])
def market_rates_daily():
    return g.finalize(g.build(spark, g.gen_market_rates_daily()), "market_rates_daily")


@mv(name="advance_pricing_daily", comment=g.COMMENTS["advance_pricing_daily"]["table"])
def advance_pricing_daily():
    return g.finalize(g.build(spark, g.gen_advance_pricing_daily()), "advance_pricing_daily")


@mv(name="co_issuances", comment=g.COMMENTS["co_issuances"]["table"])
def co_issuances():
    return g.finalize(g.build(spark, g.gen_co_issuances()), "co_issuances")


@mv(name="bank_position_daily", comment=g.COMMENTS["bank_position_daily"]["table"])
def bank_position_daily():
    return g.finalize(g.build(spark, g.gen_bank_position_daily()), "bank_position_daily")


@mv(name="investment_holdings", comment=g.COMMENTS["investment_holdings"]["table"])
def investment_holdings():
    return g.finalize(g.build(spark, g.gen_investment_holdings()), "investment_holdings")


@mv(name="prepayment_speeds", comment=g.COMMENTS["prepayment_speeds"]["table"])
def prepayment_speeds():
    return g.finalize(g.build(spark, g.gen_prepayment_speeds()), "prepayment_speeds")
