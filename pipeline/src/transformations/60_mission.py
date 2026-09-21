"""Affordable housing & mission domain.

Edges: members -> ahp_applications, homeownership_setaside, cip_cica_activity;
ahp_applications -> mission_units (units are rolled up from awarded/disbursed AHP
projects, by state).
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


@mv(name="ahp_applications", comment=g.COMMENTS["ahp_applications"]["table"])
def ahp_applications():
    base = g.build(spark, g.gen_ahp_applications())
    base = g.edge(spark, base, "members", "member_id")
    return g.finalize(base, "ahp_applications")


@mv(name="homeownership_setaside", comment=g.COMMENTS["homeownership_setaside"]["table"])
def homeownership_setaside():
    base = g.build(spark, g.gen_homeownership_setaside())
    base = g.edge(spark, base, "members", "member_id")
    return g.finalize(base, "homeownership_setaside")


@mv(name="cip_cica_activity", comment=g.COMMENTS["cip_cica_activity"]["table"])
def cip_cica_activity():
    base = g.build(spark, g.gen_cip_cica_activity())
    base = g.edge(spark, base, "members", "member_id")
    return g.finalize(base, "cip_cica_activity")


@mv(name="mission_units", comment=g.COMMENTS["mission_units"]["table"])
def mission_units():
    base = g.build(spark, g.gen_mission_units())
    base = g.edge(spark, base, "ahp_applications", "state")
    return g.finalize(base, "mission_units")


@mv(name="pledge_activity", comment=g.COMMENTS["pledge_activity"]["table"])
def pledge_activity():
    return g.finalize(g.build(spark, g.gen_pledge_activity()), "pledge_activity")
