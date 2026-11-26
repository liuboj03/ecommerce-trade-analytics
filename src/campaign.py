"""Campaign review: promo week vs the average week of the baseline period.

GMV = buyers x orders per buyer x AOV. Taking logs turns the product into a sum,
so each factor's share of the GMV change is ln(factor ratio) / ln(GMV ratio).
"""
import math

import duckdb
import pandas as pd

from . import config


def _period_kpis(con, start: str, end: str, weeks: float) -> dict:
    gmv, orders, buyers = con.execute(
        """
        SELECT SUM(item_amount), COUNT(*), COUNT(DISTINCT customer_unique_id)
        FROM dwd_order
        WHERE is_valid AND purchase_date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
        """, [start, end]).fetchone()
    # buyers are counted over the whole period, then scaled to an average week
    return {"gmv": gmv / weeks, "orders": orders / weeks, "buyers": buyers / weeks}


def review(con: duckdb.DuckDBPyConnection) -> dict:
    c = config.CAMPAIGN
    base_days = (pd.Timestamp(c["baseline_end"]) - pd.Timestamp(c["baseline_start"])).days + 1
    promo_days = (pd.Timestamp(c["promo_end"]) - pd.Timestamp(c["promo_start"])).days + 1
    base = _period_kpis(con, c["baseline_start"], c["baseline_end"], base_days / 7)
    promo = _period_kpis(con, c["promo_start"], c["promo_end"], promo_days / 7)

    for k in (base, promo):
        k["orders_per_buyer"] = k["orders"] / k["buyers"]
        k["aov"] = k["gmv"] / k["orders"]

    kpi = pd.DataFrame({"baseline_week_avg": base, "promo_week": promo})
    kpi["change"] = kpi["promo_week"] / kpi["baseline_week_avg"] - 1

    total = math.log(promo["gmv"] / base["gmv"])
    decomposition = pd.DataFrame([
        {"driver": d, "log_change": math.log(promo[d] / base[d]),
         "share_of_gmv_change": math.log(promo[d] / base[d]) / total}
        for d in ("buyers", "orders_per_buyer", "aov")
    ])

    categories = con.execute(
        """
        WITH g AS (
            SELECT category,
                   SUM(price) FILTER (WHERE purchase_date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)) AS promo_gmv,
                   SUM(price) FILTER (WHERE purchase_date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)) / ? AS base_week_gmv
            FROM dwd_order_item
            WHERE is_valid
            GROUP BY category
        )
        SELECT category,
               COALESCE(promo_gmv, 0)                              AS promo_gmv,
               COALESCE(base_week_gmv, 0)                          AS baseline_week_gmv,
               COALESCE(promo_gmv, 0) - COALESCE(base_week_gmv, 0) AS incremental_gmv
        FROM g
        ORDER BY incremental_gmv DESC
        """,
        [c["promo_start"], c["promo_end"], c["baseline_start"], c["baseline_end"], base_days / 7],
    ).df()
    categories["share_of_increment"] = categories["incremental_gmv"] / categories["incremental_gmv"].sum()

    return {"kpi": kpi, "decomposition": decomposition, "categories": categories}
